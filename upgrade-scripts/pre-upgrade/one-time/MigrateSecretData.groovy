void call() {

    String oldSecretName = "redash-setup-secret"
    String newSecretName = "redash-system-admin-creds"
    //Check if deprecated secret exists
    String secretStatus = sh(script: "oc -n $NAMESPACE get secret $oldSecretName 2> /dev/null", returnStatus: true)
    if (secretStatus == '0') {

        //Get current system admin user password
        String currentPassword = sh(script: "oc get secret $oldSecretName -o jsonpath={.data.password} " +
                "-n $NAMESPACE | base64 --decode", returnStdout: true)

        //Generate new email for system admin user
        String newEmail = "${UUID.randomUUID()}@mail.com"
        sh(script: "set +x; oc -n $NAMESPACE create secret generic $newSecretName \
      --from-literal=email=$newEmail \
      --from-literal=password=$currentPassword;")

        //Update system admin user email in Redash db
        String redashDbPassword = sh(script: "oc get secret redash-secrets -o jsonpath={.data.postgresqlPassword} " +
                "-n $NAMESPACE | base64 --decode", returnStdout: true)
        String psqlCommand = "\\\"UPDATE users SET email='$newEmail' WHERE id=1;\\\""
        String bashCommand = "\"export PGPASSWORD=$redashDbPassword; psql -d redash -U redash -c $psqlCommand\""
                ["admin", "viewer"].each {
            sh(script: "set +x; oc exec redash-$it-postgresql-0 -n $NAMESPACE -- bash -c $bashCommand")
        }
        //Patch secret
        sh(script: "oc annotate --overwrite secret $newSecretName meta.helm.sh/release-name='redash-chart' -n $NAMESPACE || :")
        sh(script: "oc annotate --overwrite secret $newSecretName meta.helm.sh/release-namespace=$NAMESPACE -n $NAMESPACE || :")
        sh(script: "oc label secret $newSecretName app.kubernetes.io/managed-by='Helm' -n $NAMESPACE || :")
        //Remove deprecated secret
        sh(script: "oc -n $NAMESPACE delete secret redash-setup-secret --ignore-not-found")
    }
}

return this;
