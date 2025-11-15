pipeline {
    agent any

    environment {
        OWNER       = "Greenapple0101"
        REPO        = "conversation-service"
        GITHUB_REPO = "https://github.com/devops-healthyreal/conversation-service.git"

        // GitHub Personal Access Token (Credential ID)
        GITHUB_PAT  = credentials('healthy-real')

        // Docker image name
        IMAGE_NAME = "conversation-conv"

        // DEV server
        DEV_HOST = "3.34.155.126"
        DEV_USER = "ubuntu"
        DEV_DIR  = "/home/ubuntu/conversation-dev"

        // PROD server
        PROD_HOST = "13.124.109.82"
        PROD_USER = "ubuntu"
        PROD_DIR  = "/home/ubuntu/conversation-prod"
    }

    stages {

        /* ============================================================
         * 1) 체크아웃 — 현재 빌드되는 브랜치 그대로 가져오기
         * ============================================================ */
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    echo "Current Branch: ${env.BRANCH_NAME}"
                }
            }
        }

        /* ============================================================
         * 2) DEVELOP — SonarQube 분석
         * ============================================================ */
        stage('SonarQube Analysis') {
            when { branch 'develop' }
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh """
                        sonar-scanner \
                          -Dsonar.projectKey=conversation-service \
                          -Dsonar.sources=. \
                          -Dsonar.host.url=${SONAR_HOST_URL} \
                          -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }

        /* ============================================================
         * 3) DEVELOP — Quality Gate 확인
         * ============================================================ */
        stage('Quality Gate') {
            when { branch 'develop' }
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Quality Gate failed: ${qg.status}"
                        }
                    }
                }
            }
        }

        /* ============================================================
         * 4) DEVELOP — Dev 서버 배포
         * ============================================================ */
        stage('Deploy to DEV') {
            when { branch 'develop' }
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        docker build -t ${IMAGE_NAME}:dev .
                        docker save ${IMAGE_NAME}:dev | gzip > image.tar.gz

                        scp -o StrictHostKeyChecking=no image.tar.gz ${DEV_USER}@${DEV_HOST}:${DEV_DIR}/

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
         * 5) DEVELOP — JMeter 부하 테스트
         * ============================================================ */
        stage('Load Test') {
            when { branch 'develop' }
            steps {
                sh """
                    jmeter -n -t loadtest.jmx -l results.jtl
                """
            }
        }

        /* ============================================================
         * 6) DEVELOP — 부하 테스트 통과 시 main 자동 merge
         * ============================================================ */
        stage('Auto Merge to Main') {
            when { branch 'develop' }
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
         * 7) MAIN — 운영 서버 배포
         * ============================================================ */
        stage('Deploy to PROD') {
            when { branch 'main' }
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        docker build -t ${IMAGE_NAME}:latest .
                        docker save ${IMAGE_NAME}:latest | gzip > image.tar.gz

                        scp -o StrictHostKeyChecking=no image.tar.gz ${PROD_USER}@${PROD_HOST}:${PROD_DIR}/

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
