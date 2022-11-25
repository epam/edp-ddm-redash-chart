void call() {
    String secretStatus = sh(script: "oc -n $NAMESPACE get secret redash-secrets 2> /dev/null", returnStatus: true)
    if (secretStatus != '0') {
        String currentSecretKey = sh(script: "oc get secret redash-chart-redash-admin -o jsonpath={.data.secretKey} " +
                "-n $NAMESPACE | base64 --decode", returnStdout: true)
        String currentCookieSecret = sh(script: "oc get secret redash-chart-redash-admin -o jsonpath={.data.cookieSecret} " +
                "-n $NAMESPACE | base64 --decode", returnStdout: true)
        String currentPostgresPassword = sh(script: "oc get secret redash-chart-postgresql -o jsonpath={.data.postgresql-password} " +
                "-n $NAMESPACE | base64 --decode", returnStdout: true)
        sh(script: "oc -n $NAMESPACE create secret generic redash-secrets \
      --from-literal=secretKey=\"$currentSecretKey\" \
      --from-literal=cookieSecret=\"$currentCookieSecret\" \
      --from-literal=postgresqlPassword=\"$currentPostgresPassword\" \
      --from-literal=googleClientSecret='notset' \
      --from-literal=ldapBindDnPassword='notset' \
      --from-literal=mailPassword='notset';")
    }
}

return this;