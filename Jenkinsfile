pipeline {
    agent any

    environment {
        // ✅ 환경 변수 정의
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')  // 젠킨스에 등록된 DockerHub ID/PW
        
        DOCKER_IMAGE = "devops-healthyreal/conversation"
        IMAGE_TAG = "latest"
        
        DEPLOY_USER = "ubuntu"
        DEPLOY_SERVER = "3.34.155.126"       // k3s 워커노드 서버 IP
        DEPLOY_PATH = "/home/ubuntu/k3s-deploy" // kubectl apply 실행 경로
        
        // SonarCloud credentials
        SONAR_TOKEN = credentials('SONAR_TOKEN')
        SONAR_ORG   = credentials('SONAR_ORG')
        SONAR_PROJECT_KEY = credentials('SONAR_PROJECT_KEY')
    }

    stages {

        /* ============================================================
         * 1) Checkout + 브랜치 자동 감지
         * ============================================================ */
        stage('Checkout') {
            steps {
                echo "📦 GitHub에서 소스코드 가져오기"
                checkout scm
                
                // Shallow clone 방지 (git blame 정보를 위해 전체 히스토리 필요)
                sh "git fetch --unshallow || true"

                script {
                    if (env.GIT_BRANCH) {
                        env.BRANCH_NAME = env.GIT_BRANCH.replace("origin/", "")
                    } else {
                        env.BRANCH_NAME = sh(
                            script: "git rev-parse --abbrev-ref HEAD",
                            returnStdout: true
                        ).trim()
                    }
                    echo "Detected Branch: ${env.BRANCH_NAME}"
                }
            }
        }

        /* ============================================================
         * 2) DEVELOP - Test & Coverage
         * ============================================================ */
        stage('Test & Coverage') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                echo "🧪 테스트 및 커버리지 수집 중..."
                sh """
                    python3 -m venv venv
                    . venv/bin/activate

                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov

                    pytest \
                      --timeout=30 \
                      --cov=. \
                      --cov-report=xml:${WORKSPACE}/coverage.xml \
                      --cov-report=term
                """
            }
        }

        /* ============================================================
         * 3) DEVELOP - SonarCloud 분석
         * ============================================================ */
        stage('SonarCloud Analysis') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                echo "🔍 SonarCloud 코드 품질 분석 중..."
                script {
                    def scannerHome = tool 'sonar-scanner'
                    sh """
                        export PATH=${scannerHome}/bin:\$PATH
                        ${scannerHome}/bin/sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                          -Dsonar.organization=${SONAR_ORG} \
                          -Dsonar.sources=api,app.py \
                          -Dsonar.projectBaseDir=${WORKSPACE} \
                          -Dsonar.python.coverage.reportPaths=${WORKSPACE}/coverage.xml \
                          -Dsonar.exclusions=venv/**,**/venv/**,**/__pycache__/**,**/*.pyc,**/tests/**,**/node_modules/**,**/.git/** \
                          -Dsonar.scm.provider=git \
                          -Dsonar.scm.exclusions.disabled=true \
                          -Dsonar.host.url=https://sonarcloud.io \
                          -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }

        /* ============================================================
         * 4) DEVELOP — Quality Gate
         * ============================================================ */
        stage('Quality Gate') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                echo "✅ Quality Gate 확인 중..."
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        try {
                            def qg = waitForQualityGate abortPipeline: true
                            if (qg.status != 'OK') {
                                error "Quality Gate failed: ${qg.status}"
                            }
                            echo "Quality Gate passed: ${qg.status}"
                        } catch (Exception e) {
                            echo "Quality Gate check failed: ${e.getMessage()}"
                            error "Quality Gate check failed: ${e.getMessage()}"
                        }
                    }
                }
            }
        }

        /* ============================================================
         * 5) MAIN — Docker Build
         * ============================================================ */
        stage('Build Docker Image') {
            when { expression { env.BRANCH_NAME == 'main' } }
            steps {
                echo "🐳 도커 이미지 빌드 중..."
                sh """
                    docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .
                """
            }
        }

        /* ============================================================
         * 6) MAIN — Docker Push (Docker Hub)
         * ============================================================ */
        stage('Login & Push Docker Image') {
            when { expression { env.BRANCH_NAME == 'main' } }
            steps {
                echo "🚀 DockerHub 로그인 및 이미지 푸시"
                script {
                    // Docker Hub credentials에서 사용자명 추출 (credentials ID에서 추출하거나 별도로 관리)
                    // 참고: credentials('dockerhub-credentials')는 usernamePassword 타입이어야 함
                    withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh """
                            echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin
                            docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        /* ============================================================
         * 7) MAIN — Sync YAML to Server
         * ============================================================ */
        stage('Sync YAML to Server') {
            when { expression { env.BRANCH_NAME == 'main' } }
            steps {
                echo "🗂️ k8s YAML 파일을 서버로 동기화 (덮어쓰기 또는 신규 생성)"
                script {
                    sshagent(credentials: ['admin']) {
                        // 서버에 k8s 폴더가 없으면 만들고, yaml 파일 복사
                        sh """
                            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                                mkdir -p ${DEPLOY_PATH}
                            '
                            scp -o StrictHostKeyChecking=no k8s/deployment.yaml ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/deployment.yaml
                            scp -o StrictHostKeyChecking=no k8s/service.yaml ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/service.yaml
                        """
                    }
                }
            }
        }

        /* ============================================================
         * 8) MAIN — Deploy to k3s Cluster
         * ============================================================ */
        stage('Deploy to k3s Cluster') {
            when { expression { env.BRANCH_NAME == 'main' } }
            steps {
                echo "⚙️ 원격 서버에 배포(kubectl apply -f)"
                script {
                    sshagent(credentials: ['admin']) {
                        // SSH를 통해 원격 서버에서 kubectl 명령 실행
                        // kubectl set image를 먼저 시도하고, 실패하면 kubectl apply 실행
                        sh """
                            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                                echo "🔄 최신 Docker 이미지로 배포 중..."
                                kubectl set image deployment/conversation conversation=${DOCKER_IMAGE}:${IMAGE_TAG} --record || \\
                                kubectl apply -f ${DEPLOY_PATH}/deployment.yaml
                                
                                echo "📡 Service 배포 중..."
                                kubectl apply -f ${DEPLOY_PATH}/service.yaml
                                
                                echo "🔄 Deployment 재시작 중..."
                                kubectl rollout restart deployment conversation
                                kubectl rollout status deployment conversation --timeout=300s
                                
                                echo "✅ 배포 완료"
                            '
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "🎉 배포 성공!"
        }
        failure {
            echo "❌ 배포 실패. 로그를 확인하세요."
        }
    }
}
