void call() {
    GString cli = "oc -n ${NAMESPACE}"
    ArrayList<String> resourcesPrefixList  = ["role.rbac.authorization.k8s.io/migrate-redash-script-one-time",
                                              "rolebinding.rbac.authorization.k8s.io/migrate-redash-script-one-time",
                                              "serviceaccount/migrate-redash-script-one-time",
                                              "configmap/migrate-redash-script-one-time",
                                              "job.batch/migrate-redash-script-one-time",
                                              "pvc/data-redash"

    ]

    resourcesPrefixList.each { resourcePrefix ->
        ["admin", "viewer"].each { instance ->
            String resourceName = resourcePrefix.startsWith("pvc/") ? "${resourcePrefix}-${instance}-postgresql-0"  : "${resourcePrefix}-${instance}"
            def checkResourceExist = sh(script: "${cli} get ${resourceName}"
                    + " --ignore-not-found", returnStdout: true)
            if (checkResourceExist) {
                sh "${cli} delete ${resourceName}"
            }
        }
    }
}

return this;
