void call() {

    String oldSecretName = "redash-secrets"
    //Check if deprecated secret exists
    String secretStatus = sh(script: "oc -n $NAMESPACE get secret $oldSecretName 2> /dev/null", returnStatus: true)
    if (secretStatus == '0') {

        //Get current passwords
        LinkedHashMap currentPasswords = ["secretKey"         : "secretKey", "cookieSecret": "cookieSecret",
                                          "postgresqlPassword": "postgresqlPassword", "googleClientSecret": "googleClientSecret",
                                          "ldapBindDnPassword": "ldapBindDnPassword", "mailPassword": "mailPassword"]

        ["secretKey", "cookieSecret", "postgresqlPassword", "googleClientSecret", "ldapBindDnPassword", "mailPassword"].each {
            String oldSecretData = ".data." + "${it}"
            currentPasswords[it] = sh(script: "oc -n $NAMESPACE get secret redash-secrets -o jsonpath={\\$oldSecretData} | base64 --decode", returnStdout: true)
        }

        //Create new secrets
        ["redash-admin-secret", "redash-viewer-secret"].each {
            String newSecretData = "--from-literal=secretKey=" + currentPasswords["secretKey"] + " --from-literal=cookieSecret=" + currentPasswords["cookieSecret"] +
                    " --from-literal=postgresqlPassword=" + currentPasswords["postgresqlPassword"] + " --from-literal=googleClientSecret=" + currentPasswords["googleClientSecret"] +
                    " --from-literal=ldapBindDnPassword=" + currentPasswords["ldapBindDnPassword"] + " --from-literal=mailPassword=" + currentPasswords["mailPassword"]
            sh(script: "set +x; oc -n $NAMESPACE create secret generic $it $newSecretData")
            sh(script: "oc label secret $it app.kubernetes.io/managed-by='Helm' -n $NAMESPACE")
            sh(script: "oc annotate --overwrite secret $it meta.helm.sh/release-name='redash-chart' -n $NAMESPACE")
            sh(script: "oc annotate --overwrite secret $it meta.helm.sh/release-namespace='$NAMESPACE' -n $NAMESPACE")
        }

        //Remove old secret
        String adminSecretStatus = sh(script: "oc -n $NAMESPACE get secret redash-admin-secret 2> /dev/null", returnStatus: true)
        String viewerSecretStatus = sh(script: "oc -n $NAMESPACE get secret redash-viewer-secret 2> /dev/null", returnStatus: true)
        if (adminSecretStatus == '0' && viewerSecretStatus == '0') {
            sh(script: "oc -n $NAMESPACE delete secret $oldSecretName")
        }
    }
}

return this;
