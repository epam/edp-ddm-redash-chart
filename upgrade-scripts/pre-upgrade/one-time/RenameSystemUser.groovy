void call() {

    //Update user name in Redash db
    String redashViewerDbPassword = sh(script: "oc get secret redash-viewer-secret -o jsonpath={.data.postgresqlPassword} " +
            "-n $NAMESPACE | base64 --decode", returnStdout: true)
    String psqlCommand = "\\\"UPDATE users SET name='system-admin-user-do-not-disable' WHERE id=1;\\\""
    String viewerBashCommand = "\"export PGPASSWORD=$redashViewerDbPassword; psql -d redash -U redash -c $psqlCommand\""
    sh(script: "set +x; oc exec redash-viewer-postgresql-0 -n $NAMESPACE -- bash -c $viewerBashCommand")

    String isAdminInstanceExists = sh(script: "oc -n $NAMESPACE get pod redash-admin-postgresql-0 2> /dev/null", returnStatus: true)
    if (isAdminInstanceExists == '0') {
        String redashAdminDbPassword = sh(script: "oc get secret redash-admin-secret -o jsonpath={.data.postgresqlPassword} " +
                "-n $NAMESPACE | base64 --decode", returnStdout: true)
        String AdminPsqlCommand = "\\\"UPDATE users SET name='system-admin-user-do-not-disable' WHERE id=1;\\\""
        String adminBashCommand = "\"export PGPASSWORD=$redashAdminDbPassword; psql -d redash -U redash -c $AdminPsqlCommand\""
        sh(script: "set +x; oc exec redash-admin-postgresql-0 -n $NAMESPACE -- bash -c $adminBashCommand")
    }
}

return this;
