import Axios from 'axios';

const authClient = Axios.create({
    baseURL: '',
    withCredentials: true,
    headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Authorization': "Bearer " + localStorage.getItem('token')
    }
})

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
    auth() {
        return authClient.get('/auth/authenticated')
    },
    dashboardData() {
        return apiClient.get('/')
    },
    getConfig() {
        return apiClient.get('/initial_config')
    },
    initial_config(bot_token, chat_id, vcs_host, vcs_token, domain, repos) {
        return apiClient.post('/initial_config', {
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
    },
    logout() {
        return authClient.get('/auth/logout')
    }
}