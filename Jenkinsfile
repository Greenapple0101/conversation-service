pipeline {
    agent any

    environment {
        OWNER       = "Greenapple0101"
        REPO        = "conversation-service"
        GITHUB_REPO = "https://github.com/devops-healthyreal/conversation-service.git"

        GITHUB_PAT  = credentials('healthy-real')
        IMAGE_NAME  = "conversation-conv"

        DEV_HOST = "13.54.10.35"
        DEV_USER = "ubuntu"
        DEV_DIR  = "/home/ubuntu/conversation-dev"

        PROD_HOST = "13.124.109.82"
        PROD_USER = "ubuntu"
        PROD_DIR  = "/home/ubuntu/conversation-prod"

        SONAR_TOKEN = credentials('sonar-token')
        SONAR_HOST_URL = "http://13.211.124.66:9000"
    }

    stages {

        /* ============================================================
         * 1) Checkout + 브랜치 자동 감지
         * ============================================================ */
        stage('Checkout') {
            steps {
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
         * 3) DEVELOP - SonarQube 분석
         * ============================================================ */
        stage('SonarQube Analysis') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                script {
                    // SonarQube 헬스 체크 - 완전히 준비될 때까지 대기
                    echo "SonarQube 헬스 체크 시작..."
                    def maxWaitTime = 120  // 최대 2분 대기
                    def waitTime = 0
                    def isReady = false
                    
                    while (waitTime < maxWaitTime && !isReady) {
                        try {
                            def status = sh(
                                script: "curl -s ${SONAR_HOST_URL}/api/system/status | grep -o '\"status\":\"[^\"]*\"' | cut -d'\"' -f4",
                                returnStdout: true
                            ).trim()
                            
                            if (status == "UP") {
                                echo "SonarQube가 준비되었습니다. (상태: ${status})"
                                isReady = true
                            } else {
                                echo "SonarQube 대기중... (현재 상태: ${status}, 대기 시간: ${waitTime}초)"
                                sleep(5)
                                waitTime += 5
                            }
                        } catch (Exception e) {
                            echo "SonarQube 연결 시도 중... (대기 시간: ${waitTime}초)"
                            sleep(5)
                            waitTime += 5
                        }
                    }
                    
                    if (!isReady) {
                        error "SonarQube가 ${maxWaitTime}초 내에 준비되지 않았습니다."
                    }
                }
                
                withSonarQubeEnv('sonarqube') {
                    script {
                        def scannerHome = tool 'sonar-scanner'
                        sh """
                            export PATH=${scannerHome}/bin:\$PATH
                            ${scannerHome}/bin/sonar-scanner \
                              -Dsonar.projectKey=conversation-service \
                              -Dsonar.projectName=conversation-service \
                              -Dsonar.sources=api,app.py \
                              -Dsonar.projectBaseDir=${WORKSPACE} \
                              -Dsonar.python.coverage.reportPaths=${WORKSPACE}/coverage.xml \
                              -Dsonar.exclusions=venv/**,**/venv/**,**/__pycache__/**,**/*.pyc,**/tests/**,**/node_modules/**,**/.git/** \
                              -Dsonar.scm.provider=git \
                              -Dsonar.scm.exclusions.disabled=true \
                              -Dsonar.host.url=$SONAR_HOST_URL \
                              -Dsonar.login=$SONAR_TOKEN
                        """
                    }
                }
            }
        }

        /* ============================================================
         * 4) DEVELOP — Quality Gate
         * ============================================================ */
        stage('Quality Gate') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    withSonarQubeEnv('sonarqube') {
                        script {
                            try {
                                def qg = waitForQualityGate abortPipeline: true
                                if (qg.status != 'OK') {
                                    error "Quality Gate failed: ${qg.status}"
                                }
                            } catch (Exception e) {
                                echo "Quality Gate check failed: ${e.getMessage()}"
                                error "Quality Gate check failed: ${e.getMessage()}"
                            }
                        }
                    }
                }
            }
        }

        /* ============================================================
         * 5) DEVELOP — DEV 서버 배포
         * ============================================================ */
        stage('Deploy to DEV') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                sshagent(credentials: ['new-server']) {
                    sh """
                        docker build -t ${IMAGE_NAME}:dev .
                        docker save ${IMAGE_NAME}:dev | gzip > image.tar.gz

                        ssh -o StrictHostKeyChecking=no ${DEV_USER}@${DEV_HOST} "mkdir -p ${DEV_DIR}"
                        scp -o StrictHostKeyChecking=no image.tar.gz ${DEV_USER}@${DEV_HOST}:${DEV_DIR}/image.tar.gz

                        ssh -o StrictHostKeyChecking=no ${DEV_USER}@${DEV_HOST} "
                            cd ${DEV_DIR}
                            gunzip -c image.tar.gz | docker load
                            docker stop dev-conv || true
                            docker rm dev-conv || true
                            docker run -d -p 8000:8000 --name dev-conv ${IMAGE_NAME}:dev
                        "
                    """
                }
            }
        }

        /* ============================================================
         * 6) DEVELOP — Load Test (JMeter) + Performance Gate (p95)
         * ============================================================ */
        stage('Load Test') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                script {
                    // 서버 준비 대기 (컨테이너가 완전히 시작될 때까지)
                    echo "Waiting for DEV server to be ready..."
                    sh "sleep 10"
                    
                    // JMX 파일의 IP를 환경변수로 동적 교체 (확실하게 올바른 서버 타겟)
                    // 혹시 이전 버전의 잘못된 IP(13.211.124.66)가 있으면 모두 올바른 IP로 교체
                    sh """
                        # 잘못된 IP를 모두 올바른 IP로 교체
                        sed -i.bak 's/13\\.211\\.124\\.66/${DEV_HOST}/g' ${WORKSPACE}/loadtest.jmx
                        echo "JMX file updated: Target server = ${DEV_HOST}:8000"
                        # 확인용 출력
                        grep -n "HTTPSampler.domain" ${WORKSPACE}/loadtest.jmx || true
                    """
                    
                    // JMeter 실행 (절대 경로 사용 - 가장 안전한 방식)
                    sh """
                        /opt/jmeter/bin/jmeter -n -t ${WORKSPACE}/loadtest.jmx -l ${WORKSPACE}/results.jtl -JDEV_HOST=${DEV_HOST} -JDEV_PORT=8000
                    """
                    
                    // p95 응답시간 계산 및 성능 Gate 체크
                    def p95Threshold = 2000  // 2초 (밀리초)
                    
                    // Python 스크립트 실행 (3중 작은따옴표로 들여쓰기 문제 해결)
                    def result = sh(
                        script: '''
python3 << 'EOF'
import csv
import sys

threshold = 2000
response_times = []

try:
    with open('results.jtl', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('elapsed') and row.get('success', '').lower() == 'true':
                try:
                    response_times.append(int(float(row['elapsed'])))
                except (ValueError, KeyError):
                    pass
    
    if not response_times:
        print("ERROR: No valid response times found")
        sys.exit(1)
    
    # p95 계산
    sorted_times = sorted(response_times)
    p95_index = int(len(sorted_times) * 0.95)
    p95_value = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
    
    print(f"Total requests: {len(response_times)}")
    print(f"p95 response time: {p95_value}ms")
    print(f"Threshold: {threshold}ms")
    
    if p95_value > threshold:
        print(f"FAILED: p95 ({p95_value}ms) exceeds threshold ({threshold}ms)")
        sys.exit(1)
    else:
        print(f"PASSED: p95 ({p95_value}ms) is within threshold ({threshold}ms)")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
EOF
                        ''',
                        returnStatus: true
                    )
                    
                    if (result != 0) {
                        error("Performance Gate FAILED: p95 response time exceeds threshold (${p95Threshold}ms)")
                    } else {
                        echo("Performance Gate PASSED: p95 response time is within threshold")
                    }
                }
            }
        }

        /* ============================================================
         * 7) DEVELOP — Auto Merge to Main
         * ============================================================ */
        stage('Auto Merge to Main') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                script {
                    def pr_num = sh(
                        script: """
                            curl -s -H "Authorization: token ${GITHUB_PAT}" \
                            https://api.github.com/repos/${OWNER}/${REPO}/pulls?state=open&base=main \
                            | jq '.[0].number'
                        """,
                        returnStdout: true
                    ).trim()

                    if (pr_num == "null" || pr_num == "") {
                        error "No open PR for merging into main."
                    }

                    env.PR_NUMBER = pr_num

                    sh """
                        curl -X PUT \
                          -H "Authorization: token ${GITHUB_PAT}" \
                          -H "Accept: application/vnd.github.v3+json" \
                          https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/merge \
                          -d '{"merge_method":"merge"}'
                    """
                }
            }
        }

        /* ============================================================
         * 8) MAIN — PROD 배포
         * ============================================================ */
        stage('Deploy to PROD') {
            when { expression { env.BRANCH_NAME == 'main' } }
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        docker build -t ${IMAGE_NAME}:latest .
                        docker save ${IMAGE_NAME}:latest | gzip > image.tar.gz

                        ssh -o StrictHostKeyChecking=no ${PROD_USER}@${PROD_HOST} "mkdir -p ${PROD_DIR}"
                        scp -o StrictHostKeyChecking=no image.tar.gz ${PROD_USER}@${PROD_HOST}:${PROD_DIR}/image.tar.gz

                        ssh -o StrictHostKeyChecking=no ${PROD_USER}@${PROD_HOST} "
                            cd ${PROD_DIR}
                            gunzip -c image.tar.gz | docker load
                            docker stop conversation || true
                            docker rm conversation || true
                            docker run -d -p 8000:8000 --name conversation ${IMAGE_NAME}:latest
                        "
                    """
                }
            }
        }
    }
}
