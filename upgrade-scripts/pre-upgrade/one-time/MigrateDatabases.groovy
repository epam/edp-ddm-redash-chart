void call() {
    GString cli = "oc -n ${NAMESPACE}"
    String analyticalDBPodName = sh(script: "${cli} get pods " +
            "-l postgres-operator.crunchydata.com/cluster=analytical,postgres-operator.crunchydata.com/role=master" +
            " --no-headers -o custom-columns=\"NAME:.metadata.name\"", returnStdout: true).trim()

    ["admin", "viewer"].each { name ->
        String databasePodName = "redash-" + name + "-postgresql-0"
        String databaseUser = "redash_" + name + "_role"
        String databaseSecretName = "redash-" + name + "-secret"
        String dockerURL = "${edpComponentDockerRegistryUrl}\\/${globalEDPProject}"
        String filekeeper = "templates/job-database-migration.yaml"
        sh "cp ${filekeeper} ${filekeeper}.orig"
        String destFile = name + "-job-database-migration.yaml"
        sh "sed 's/INSTANCE_NAME/${name}/g' ${filekeeper}.orig > ${filekeeper}.tmp"
        sh "sed 's/REPLACE_ANALYTICAL_POD/${analyticalDBPodName}/g' ${filekeeper}.tmp > ${filekeeper}.orig"
        sh "sed 's/REPLACE_REDASHQL_POD_NAME/${databasePodName}/g' ${filekeeper}.orig > ${filekeeper}.tmp"
        sh "sed 's/REPLACE_USER/${databaseUser}/g' ${filekeeper}.tmp > ${filekeeper}.orig"
        sh "sed 's#DOCKER_URL#'${dockerURL}'#g' ${filekeeper}.orig > ${filekeeper}.tmp"
        sh "sed 's/DATABASE_SECRET_NAME/'${databaseSecretName}'/g' ${filekeeper}.tmp > ${destFile}"
        sh "${cli} apply -f ${destFile}"
        sh "rm ${destFile} ${filekeeper}.orig"
    }
}


return this;
