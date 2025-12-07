pipeline {
    agent any

    environment {
        DOCKERHUB = credentials('dockerhub-credentials')

        SONAR_TOKEN = credentials('sonar-token')
        SONAR_ORG   = credentials('SONAR_ORG')
        SONAR_PROJECT_KEY = credentials('SONAR_PROJECT_KEY')

        GITHUB_TOKEN = credentials('healthy-real')

        DOCKER_IMAGE = "yorange50/conversation"

        DEPLOY_USER = "ubuntu"
        DEPLOY_SERVER = "3.34.155.126"
        DEPLOY_PATH = "/home/ubuntu/k3s-deploy"
        YAML_FILE = "k3s-app.yaml"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        /* ✅ develop + PR + main 모두 Sonar */
        stage('SonarCloud Analysis') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH == 'origin/develop' || env.GIT_BRANCH == 'develop' }
                    expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
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

        stage('Quality Gate') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH == 'origin/develop' || env.GIT_BRANCH == 'develop' }
                    expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
                    changeRequest()
                }
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    withSonarQubeEnv('sonarqube') {
                        waitForQualityGate abortPipeline: true
                    }
                }
            }
        }

        /* ✅ develop → main PR 자동 생성 */
        stage('Auto Create PR (develop → main)') {
            when {
                expression { env.GIT_BRANCH == 'origin/develop' || env.GIT_BRANCH == 'develop' }
            }
            steps {
                sh """
                  curl -X POST https://api.github.com/repos/devops-healthyreal/conversation-service/pulls \
                    -H "Authorization: token ${GITHUB_TOKEN}" \
                    -H "Accept: application/vnd.github+json" \
                    -d '{
                      "title": "Auto PR from develop",
                      "head": "develop",
                      "base": "main",
                      "body": "✅ Sonar 통과 자동 PR"
                    }'
                """
            }
        }

        /* ✅ develop, main 에서만 빌드 */
        stage('Build Docker Image') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH == 'origin/develop' || env.GIT_BRANCH == 'develop' }
                    expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
                }
            }
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:latest ."
            }
        }

        stage('Login & Push Docker Image') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH == 'origin/develop' || env.GIT_BRANCH == 'develop' }
                    expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
                }
            }
            steps {
                sh """
                    echo ${DOCKERHUB_PSW} | docker login -u ${DOCKERHUB_USR} --password-stdin
                    docker push ${DOCKER_IMAGE}:latest
                """
            }
        }

        /* ✅ main 만 운영 배포 */
        stage('Deploy to k3s Cluster') {
            when {
                expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
            }
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                            kubectl set image deployment/conversation \
                              conversation-container=${DOCKER_IMAGE}:latest \
                            || kubectl apply -f ${DEPLOY_PATH}/${YAML_FILE}
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🎉 Sonar 통과 + PR 자동 생성 + CI/CD 성공"
        }
        failure {
            echo "❌ Sonar 실패 or PR 실패 or 배포 실패"
        }
    }
}
