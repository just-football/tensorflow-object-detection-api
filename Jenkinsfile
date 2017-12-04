ansiColor('xterm') {
    node('master') {
        deleteDir()

        stage('Checkout') {
            git branch: BRANCH_NAME, url: 'git@github.com:just-football/tensorflow-object-detection-api', credentialsId: 'jenkins'
            sh 'git checkout .'
        }

        COMMITER = sh(
          script: 'git show --format="%aN <%aE>" dev | head -n 1',
          returnStdout: true
        ).trim()

        if (COMMITER == 'JustFootball CI <ci@justfootball.io>') {
          return;
        } else {
          echo "Previous commiter was $COMMITER - Building..."
        }

        stamp = System.currentTimeMillis()

        stage('Build') {
            sh "docker build -t $stamp ."
        }

        if (BRANCH_NAME =='dev') {
            stage('Bump version') {
                VERSION = sh(
                    script: 'docker run --rm -u $(id -u):$(id -g) -v "$PWD:/app" -v "$HOME/.git:/root/.git" -w "/app" node:latest npm version patch --no-git-tag-version',
                    returnStdout: true
                ).trim()
                sshagent(['jenkins']) {
                    sh "git commit -am $VERSION"
                    sh "git tag $VERSION"
                    sh "git push --set-upstream origin dev"
                    sh "git push --tags"
                }

                echo "Version will be:$VERSION"
            }
        }

        if (BRANCH_NAME == 'dev' || BRANCH_NAME == 'master') {
            stage('Dependencies') {
                sh 'curl -OL https://github.com/kubernetes/kops/releases/download/1.5.3/kops-linux-amd64'
                sh 'mv kops-linux-amd64 kops'
                sh 'chmod +x kops'
                sh 'curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl'
                sh 'chmod +x kubectl'
            }
        }

        if (BRANCH_NAME == 'dev') {
            stage('Deploy Dev') {
                sh "source ./k8s/dev/env.sh && VERSION=$VERSION envsubst < k8s/deployment.yml > ./deployment.yml"

                sh "aws ecr get-login --no-include-email --region eu-west-1 | sh -"

                sh "docker tag $stamp 948156567635.dkr.ecr.eu-west-1.amazonaws.com/jf/zebra-object-detection:$VERSION"
                sh "docker push 948156567635.dkr.ecr.eu-west-1.amazonaws.com/jf/zebra-object-detection:$VERSION"

                withEnv(['KOPS_STATE_STORE=s3://jf-dev-k8s-state-store']) {
                    sh './kops export kubecfg k8s.dev.justfootball.io'
                }

                sh './kubectl apply -f ./deployment.yml'
            }
        }

        if (BRANCH_NAME == 'master') {
            stage('Deploy Live') {
                VERSION = sh(
                    script: 'grep \'"version":\' package.json | cut -d\\" -f4',
                    returnStdout: true
                ).trim();

                sh "source ./k8s/live/env.sh && VERSION=v$VERSION envsubst < k8s/deployment.yml > ./deployment.yml"

                withEnv(['KOPS_STATE_STORE=s3://jf-k8s-state-store']) {
                    sh './kops export kubecfg k8s.justfootball.io'
                }

                sh './kubectl apply -f ./deployment.yml'
            }
        }
    }
}

