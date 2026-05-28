pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOY_ACTION',
            choices: ['deploy', 'none', 'test_only'],
            description: 'Действие: deploy - развернуть контейнер, test_only - только тесты'
        )
        string(
            name: 'SCENARIO_FILE',
            defaultValue: 'scenario.json',
            description: 'Файл со сценарием функционального тестирования'
        )
    }

    environment {
        IMAGE_NAME = "4ddocker/lab3:${env.BUILD_NUMBER}"
        IMAGE_LATEST = '4ddocker/lab3:latest'
        LOCAL_DATA_PATH = 'C:\\DopEdu\\ML_ITMO\\DevOpsLab\\Lab3'
        VAULT_PASSWORD = credentials('vault-password')
        DOCKER_HUB_USER = '4ddocker'
        DOCKER_HUB_PASS = credentials('docker')
        DOCKER_HUB_CRED = 'docker'
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📦 Клонирование репозитория из GitHub...'
                checkout scm
                echo '✅ Код успешно получен'
            }
        }

        stage('Create Network') {
            steps {
                bat 'docker network inspect my_network >nul 2>&1 || docker network create my_network'
            }
        }

        stage('Start PostgreSQL') {
            steps {
                echo '🐘 Запуск PostgreSQL...'
                bat '''
                    docker stop postgres || true
                    docker rm postgres || true
                    docker run -d --name postgres --network my_network \
                        -e POSTGRES_USER=ml_user \
                        -e POSTGRES_PASSWORD=StrongPassword123! \
                        -e POSTGRES_DB=ml_models \
                        postgres:15
                '''
                echo '✅ PostgreSQL запущен'
            }
        }

        stage('Copy Large Files') {
            steps {
                echo '📁 Копирование больших файлов из локальной папки...'
                bat """
                    if not exist "data" mkdir data
                    if exist "${LOCAL_DATA_PATH}\\data\\*.csv" copy "${LOCAL_DATA_PATH}\\data\\*.csv" data\\
                    if not exist "models" mkdir models
                    if exist "${LOCAL_DATA_PATH}\\models\\*.pkl" copy "${LOCAL_DATA_PATH}\\models\\*.pkl" models\\
                """
                echo '✅ Большие файлы скопированы'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '🏗️ Сборка Docker образа...'
                bat "docker build -t ${IMAGE_NAME} ."
                bat "docker tag ${IMAGE_NAME} ${IMAGE_LATEST}"
                echo '✅ Образ собран'
            }
        }

        stage('Functional Tests') {
            when {
                expression { params.DEPLOY_ACTION == 'test_only' || params.DEPLOY_ACTION == 'deploy' }
            }
            steps {
                echo '🧪 Функциональное тестирование по сценарию...'
                bat """
                    docker stop test-func-${env.BUILD_NUMBER} || true
                    docker rm test-func-${env.BUILD_NUMBER} || true
                    docker run -d --name test-func-${env.BUILD_NUMBER} -p 8889:8000 --network my_network \
                        -e VAULT_PASSWORD=${VAULT_PASSWORD} \
                        -e DB_HOST=postgres \
                        -e DB_PORT=5432 \
                        -e DB_USER=ml_user \
                        -e DB_PASSWORD=StrongPassword123! \
                        -e DB_NAME=ml_models \
                        ${IMAGE_NAME}
                    timeout /t 15 /nobreak > nul
                    curl.exe -f http://localhost:8889/health
                    docker stop test-func-${env.BUILD_NUMBER}
                    docker rm test-func-${env.BUILD_NUMBER}
                """
                echo '✅ Функциональные тесты пройдены'
            }
        }

        stage('Push to Docker Hub') {
            when {
                expression { params.DEPLOY_ACTION == 'deploy' }
            }
            steps {
                script {
                    docker.withRegistry('', DOCKER_HUB_CRED) {
                        docker.image("4ddocker/lab3:${env.BUILD_NUMBER}").push()
                        docker.image("4ddocker/lab3:latest").push()
                    }
                }
                echo '✅ Образ опубликован на Docker Hub'
            }
        }

        stage('Deploy Container') {
            when {
                expression { params.DEPLOY_ACTION == 'deploy' }
            }
            steps {
                echo '🚀 Развертывание контейнера в продакшн...'
                bat """
                    docker stop lab3-api || true
                    docker rm lab3-api || true
                    docker run -d --name lab3-api -p 8000:8000 --restart unless-stopped --network my_network \
                        -e VAULT_PASSWORD=${VAULT_PASSWORD} \
                        -e DB_HOST=postgres \
                        -e DB_PORT=5432 \
                        -e DB_USER=ml_user \
                        -e DB_PASSWORD=StrongPassword123! \
                        -e DB_NAME=ml_models \
                        ${IMAGE_LATEST}
                """
                echo '✅ Контейнер развернут'
            }
        }

        stage('Health Check') {
            when {
                expression { params.DEPLOY_ACTION == 'deploy' }
            }
            steps {
                powershell '''
                    Start-Sleep -Seconds 10
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
                        if ($response.StatusCode -eq 200) {
                            Write-Host "✅ Health check пройден"
                        } else {
                            exit 1
                        }
                    } catch {
                        Write-Host "Ошибка: $_"
                        exit 1
                    }
                '''
            }
        }
    }

    post {
        always {
            script {
                bat "docker stop test-func-${env.BUILD_NUMBER} 2>nul || exit 0"
                bat "docker rm test-func-${env.BUILD_NUMBER} 2>nul || exit 0"
                bat 'docker stop lab3-api 2>nul || exit 0'
                bat 'docker rm lab3-api 2>nul || exit 0'
                bat "docker rmi ${IMAGE_NAME} ${IMAGE_LATEST} || true"
            }
        }
        success {
            echo '🎉 Pipeline успешно выполнен!'
        }
        failure {
            echo '❌ Pipeline завершился с ошибкой. Проверьте логи выше.'
        }
    }
}