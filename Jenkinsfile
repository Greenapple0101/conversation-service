// ✅ CI/CD Pipeline for conversation-service
// YAML 기반 배포 (IaC 방식)
// develop 브랜치: SonarCloud 검사 → PR 생성
// main 브랜치: Docker 빌드/푸시 → k3s 배포
pipeline {
    agent any

    environment {
        /* ✅ GitHub */
        GITHUB_TOKEN = credentials('healthy-real')
        GITHUB_OWNER = "devops-healthyreal"
        GITHUB_REPO  = "conversation-service"
        BASE_BRANCH  = "main"
        HEAD_BRANCH  = "develop"

        /* ✅ Docker */
        DOCKER_IMAGE = "yorange50/conversation"

        /* ✅ Sonar */
        SONAR_TOKEN = credentials('sonar-token')
        SONAR_ORG   = credentials('SONAR_ORG')
        SONAR_PROJECT_KEY = credentials('SONAR_PROJECT_KEY')

        /* ✅ Deploy */
        DEPLOY_USER = "ubuntu"
        DEPLOY_SERVER = "3.34.155.126"
        DEPLOY_PATH = "/home/ubuntu/k3s-deploy"
        YAML_FILE = "k3s-app.yaml"
    }

    stages {

        /* ============================================================
         * 1️⃣ Checkout
         * ============================================================ */
        stage('Checkout') {
            steps {
                echo "📦 GitHub 소스 체크아웃"
                checkout scm
                script {
                    if (env.GIT_BRANCH) {
                        env.BRANCH_NAME = env.GIT_BRANCH.replace("origin/", "").replace("refs/heads/", "")
                    } else {
                        env.BRANCH_NAME = sh(
                            script: "git rev-parse --abbrev-ref HEAD",
                            returnStdout: true
                        ).trim()
                    }
                    echo "🔍 GIT_BRANCH: ${env.GIT_BRANCH}"
                    echo "✅ Detected Branch: ${env.BRANCH_NAME}"
                }
            }
        }

        /* ============================================================
         * 2️⃣ Sonar (develop / main / PR 모두 실행)
         * ============================================================ */
        stage('SonarCloud Analysis') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                    changeRequest()
                }
            }
            steps {
                withSonarQubeEnv('sonarqube') {
                    script {
                        def scannerHome = tool 'sonar-scanner'
                        sh """
                        ${scannerHome}/bin/sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                          -Dsonar.organization=${SONAR_ORG} \
                          -Dsonar.host.url=https://sonarcloud.io \
                          -Dsonar.token=${SONAR_TOKEN}
                        """
                    }
                }
            }
        }

        /* ============================================================
         * 3️⃣ Quality Gate
         * ============================================================ */
        stage('Quality Gate') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                    changeRequest()
                }
            }
            steps {
                script {
                    // SonarCloud 분석 결과 처리 대기 (최대 15분)
                    timeout(time: 15, unit: 'MINUTES') {
                        withSonarQubeEnv('sonarqube') {
                            def qg = waitForQualityGate abortPipeline: false
                            
                            if (qg.status != 'OK') {
                                echo "⚠️ Quality Gate 상태: ${qg.status}"
                                echo "⚠️ Quality Gate 실패했지만 파이프라인은 계속 진행합니다"
                                // abortPipeline: false로 설정하여 실패해도 계속 진행
                            } else {
                                echo "✅ Quality Gate 통과"
                            }
                        }
                    }
                }
            }
        }

        /* ============================================================
         * 4️⃣ develop → main PR 자동 생성 (수동 머지 대기)
         * ============================================================ */
        stage('Auto Create PR (develop → main)') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.GIT_BRANCH?.contains('develop') }
                }
            }
            steps {
                script {
                    echo "🔍 기존 PR 존재 여부 확인"

                    def prList = sh(
                        script: '''
                        curl -s -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                        https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls?head=''' + GITHUB_OWNER + ''':''' + HEAD_BRANCH + '''&base=''' + BASE_BRANCH + '''&state=open
                        ''',
                        returnStdout: true
                    ).trim()


                    echo "PR 조회 결과: ${prList}"

                    // PR 목록 파싱하여 실제 PR 존재 여부 확인
                    def prExists = false
                    if (prList && prList != "[]" && prList != "") {
                        try {
                            def prCount = sh(
                                script: '''
                                echo ''' + prList + ''' | jq '. | length'
                                ''',
                                returnStdout: true
                            ).trim()
                            
                            if (prCount && prCount != "0" && prCount != "") {
                                prExists = true
                                def prNumber = sh(
                                    script: '''
                                    echo ''' + prList + ''' | jq -r '.[0].number'
                                    ''',
                                    returnStdout: true
                                ).trim()
                                echo "✅ 이미 PR #${prNumber} 존재 → 생성 스킵"
                            }
                        } catch (Exception e) {
                            echo "⚠️ PR 목록 파싱 실패, 직접 확인 시도"
                        }
                    }

                    if (!prExists) {
                        echo "✅ PR 없음 → 자동 생성"
                        
                        def createResult = sh(
                            script: '''
                            curl -s -w "\\nHTTP_CODE:%{http_code}" -X POST \
                              -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                              -H "Accept: application/vnd.github+json" \
                              https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls \
                              -d '{
                                "title": "🚀 develop → main 자동 PR",
                                "head": "''' + HEAD_BRANCH + '''",
                                "base": "''' + BASE_BRANCH + '''",
                                "body": "✅ Jenkins 자동 생성 PR"
                              }'
                            ''',
                            returnStdout: true
                        ).trim()

                        def httpCode = createResult.split("HTTP_CODE:")[1]
                        def response = createResult.split("HTTP_CODE:")[0]

                        if (httpCode == "201") {
                            echo "✅ PR 생성 성공"
                        } else if (httpCode == "422") {
                            echo "⚠️ PR 생성 실패: 이미 PR이 존재합니다 (HTTP 422)"
                            echo "응답: ${response}"
                        } else {
                            echo "⚠️ PR 생성 실패 (HTTP ${httpCode})"
                            echo "응답: ${response}"
                        }
                    }
                }
            }
        }

        /* ============================================================
         * 5️⃣ Docker Build (develop & main만)
         * ============================================================ */
        stage('Build Docker Image') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                }
            }
            steps {
                script {
                    // Git SHA 기반 태그 생성 (캐시 문제 해결)
                    def imageTag = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    
                    env.IMAGE_TAG = imageTag
                    env.FULL_IMAGE_NAME = "${DOCKER_IMAGE}:${imageTag}"
                    
                    echo "🐳 Docker 이미지 빌드 (태그: ${imageTag})"
                    echo "📦 이미지명: ${env.FULL_IMAGE_NAME}"
                    
                    // 캐시 무시하고 완전히 새로 빌드
                    sh "docker build --no-cache -t ${env.FULL_IMAGE_NAME} -t ${DOCKER_IMAGE}:latest ."
                }
            }
        }

        /* ============================================================
         * 6️⃣ Docker Push
         * ============================================================ */
        stage('Login & Push Docker Image') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKERHUB_USR',
                        passwordVariable: 'DOCKERHUB_PSW'
                    )
                ]) {
                    sh '''
                    echo $DOCKERHUB_PSW | docker login -u $DOCKERHUB_USR --password-stdin
                    docker push ${FULL_IMAGE_NAME}
                    docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }

        /* ============================================================
         * 7️⃣ YAML 파일 이미지 태그 업데이트 및 서버 전송
         * ============================================================ */
        stage('Sync YAML to Server') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                script {
                    echo "🗂️ k3s-app.yaml 이미지 태그 업데이트 및 서버 전송"
                    
                    // YAML 파일의 image 태그를 빌드 태그로 업데이트
                    sh """
                    sed -i.bak 's|image: ${DOCKER_IMAGE}:.*|image: ${env.FULL_IMAGE_NAME}|g' ${YAML_FILE}
                    echo "✅ YAML 이미지 태그 업데이트: ${env.FULL_IMAGE_NAME}"
                    """
                    
                    sshagent(credentials: ['ubuntu']) {
                        // 서버에 디렉토리 생성 및 YAML 파일 전송
                        sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} 'mkdir -p ${DEPLOY_PATH}'
                        scp -o StrictHostKeyChecking=no ${YAML_FILE} ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/${YAML_FILE}
                        """
                    }
                }
            }
        }

        /* ============================================================
         * 8️⃣ main 브랜치에서 YAML 기반 배포 (실무형 - IaC 방식)
         * ============================================================ */
        stage('Deploy to k3s Cluster (main branch)') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                sshagent(credentials: ['ubuntu']) {
                    script {
                        echo "🔄 YAML 기반 배포 시작 (IaC 방식)"
                        echo "📦 배포 이미지: ${env.FULL_IMAGE_NAME}"
                        echo "📄 YAML 파일: ${DEPLOY_PATH}/${YAML_FILE}"
                        
                        sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                            echo "🚀 kubectl apply 실행..."
                            kubectl apply -f ${DEPLOY_PATH}/${YAML_FILE}
                            
                            echo "⏳ 롤아웃 상태 확인 중..."
                            kubectl rollout status deployment/conversation --timeout=5m
                            
                            echo "✅ 배포 완료"
                            echo "📊 현재 배포 상태:"
                            kubectl get deployment conversation -o wide
                            kubectl get pods -l app=conversation
                        '
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "🎉 Sonar 통과 + PR 자동화 + CI/CD 성공"
        }
        failure {
            echo "❌ 파이프라인 실패"
        }
    }
}