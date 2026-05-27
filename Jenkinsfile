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
        // Lab3
        IMAGE_NAME = "4ddocker/lab3:${env.BUILD_NUMBER}"
        IMAGE_LATEST = "4ddocker/lab3:latest"
        LOCAL_DATA_PATH = "C:\\DopEdu\\ML_ITMO\\DevOpsLab\\Lab3"
        
        // Vault password (из Jenkins credentials)
        VAULT_PASSWORD = credentials('vault-password')
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📦 Клонирование репозитория из GitHub...'
                checkout scm
                echo '✅ Код успешно получен'
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
                    docker run -d --name test-func-${env.BUILD_NUMBER} -p 8889:8000 -e VAULT_PASSWORD=${VAULT_PASSWORD} ${IMAGE_NAME}
                    timeout /t 15 /nobreak > nul
                    curl.exe -f http://localhost:8889/health
                    docker stop test-func-${env.BUILD_NUMBER}
                    docker rm test-func-${env.BUILD_NUMBER}
                """
                echo '✅ Функциональные тесты пройдены'
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
                    docker run -d --name lab3-api -p 8000:8000 --restart unless-stopped -e VAULT_PASSWORD=${VAULT_PASSWORD} ${IMAGE_LATEST}
                """
                echo '✅ Контейнер развернут'
            }
        }

        stage('Health Check') {
            when {
                expression { params.DEPLOY_ACTION == 'deploy' }
            }
            steps {
                echo '🏥 Проверка здоровья развернутого контейнера...'
                bat """
                    timeout /t 10 /nobreak > nul
                    curl.exe -f http://localhost:8000/health
                """
                echo '✅ Health check пройден'
            }
        }
    }

    post {
        always {
            script {
                bat "docker stop test-func-${env.BUILD_NUMBER} 2>nul || exit 0"
                bat "docker rm test-func-${env.BUILD_NUMBER} 2>nul || exit 0"
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