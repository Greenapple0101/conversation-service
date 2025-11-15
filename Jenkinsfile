pipeline {
    agent any

    environment {
        OWNER       = "Greenapple0101"
        REPO        = "conversation-service"
        GITHUB_REPO = "https://github.com/devops-healthyreal/conversation-service.git"

        GITHUB_PAT  = credentials('healthy-real')
        IMAGE_NAME  = "conversation-conv"

        DEV_HOST = "3.34.155.126"
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
                      --cov=api \
                      --cov-report=xml:coverage.xml
                """
            }
        }

        /* ============================================================
         * 3) DEVELOP - SonarQube 분석
         * ============================================================ */
        stage('SonarQube Analysis') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                withSonarQubeEnv('sonarqube') {
                    script {
                        def scannerHome = tool 'sonar-scanner'
                        sh """
                            export PATH=${scannerHome}/bin:\$PATH
                            ${scannerHome}/bin/sonar-scanner \
                              -Dsonar.projectKey=conversation-service \
                              -Dsonar.projectName=conversation-service \
                              -Dsonar.sources=. \
                              -Dsonar.python.coverage.reportPaths=coverage.xml \
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
                    script {
                        try {
                            def qg = waitForQualityGate()
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

        /* ============================================================
         * 5) DEVELOP — DEV 서버 배포
         * ============================================================ */
        stage('Deploy to DEV') {
            when { expression { env.BRANCH_NAME == 'develop' } }
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
         * 6) DEVELOP — Load Test (JMeter)
         * ============================================================ */
        stage('Load Test') {
            when { expression { env.BRANCH_NAME == 'develop' } }
            steps {
                sh """
                    jmeter -n -t loadtest.jmx -l results.jtl
                """
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
