#!groovy

pipeline {

  agent {
    label 'lxc'
  }

  environment {
    git_commit_message = ''
    git_commit_diff = ''
    git_commit_author = ''
    git_commit_author_name = ''
    git_commit_author_email = ''
  }

  stages {

    // Build
    stage('Build') {
      steps {
        deleteDir()
        checkout scm
        sh 'make build'
      }
    }

    // Unit Tests
    stage('Unit Tests') {
      steps {
        sh "make test"
      }
    }
  }
}

