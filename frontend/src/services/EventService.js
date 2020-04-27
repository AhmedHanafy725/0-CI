import Axios from 'axios';

const apiClient = Axios.create({
    baseURL: '/api',
    withCredentials: true,
    headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Authorization': "Bearer " + localStorage.getItem('token')
    }
})

export default {
    dashboardData() {
        return apiClient.get('/')
    },
    initial_config(bot_token, chat_id, vcs_host, vcs_token, domain, repos, iyo_id, iyo_secret) {
        return apiClient.post('/initial_config', {
            iyo_id: iyo_id,
            iyo_secret: iyo_secret,
            domain: domain,
            chat_id: chat_id,
            bot_token: bot_token,
            vcs_host: vcs_host,
            vcs_token: vcs_token,
            repos: repos
        })
    },
    getBranches(repoName) {
        return apiClient.get('/repos/' + repoName)
    },
    getBranchDetails(orgName, branch) {
        return apiClient.get('/repos/' + orgName + '?branch=' + branch)
    },
    restartBuild(repo, branch) {
        return apiClient.post('/run_trigger', { repo: repo, branch: branch })
    },
    runConfig(orgName) {
        return apiClient.get('/run_config/' + orgName);
    },
    addKey(orgName, key, value) {
        if (key && value !== null) {
            return apiClient.post('/run_config/' + orgName, { key: key, value: value })
        }
    },
    deleteKey(orgName, key, value) {
        return apiClient.delete('/run_config/' + orgName, { data: { key: key, value: value } })
    },
    getBranchIdDetails(orgName, branch, id) {
        return apiClient.get('/repos/' + orgName + '?branch=' + branch + '&&id=' + id)
    },
    rebuildJob(id) {
        return apiClient.post('/run_trigger', { id: id })
    },
    getSchedulesDetails(scheduleName) {
        return apiClient.get('/schedules/' + scheduleName)
    },
    getProjectIdDetails(scheduleName, id) {
        return apiClient.get('/schedules/' + scheduleName + '?id=' + id)
    }
}
