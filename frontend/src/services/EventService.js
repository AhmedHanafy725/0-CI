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
    getBranches(repoName) {
        return apiClient.get('/repos/' + repoName)
    },
    getBranchDetails(orgName, branch) {
        return apiClient.get('/repos/' + orgName + '?branch=' + branch)
    },
    restartBuild(repo, branch) {
        return apiClient.post('/run_trigger', { repo: repo, branch: branch })
    },
    restartBuildId(id) {
        return apiClient.post('/run_trigger', { id: id })
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
    rebuildJob(name) {
        return apiClient.post('/schedule_trigger', { schedule_name: name })
    },
    getSchedulesDetails(scheduleName) {
        return apiClient.get('/schedules/' + scheduleName)
    },
    getProjectIdDetails(scheduleName, id) {
        return apiClient.get('/schedules/' + scheduleName + '?id=' + id)
    },
    logout() {
        return authClient.get('/auth/logout')
    },

    // Config APIs
    getVcs() {
        return apiClient.get('/vcs_config')
    },
    postVCS(domain, vcs_host, vcs_token) {
        return apiClient.post('/vcs_config', { domain: domain, vcs_host: vcs_host, vcs_token: vcs_token })
    },
    getCurrentRepos() {
        return apiClient.get('/repos_config')
    },
    getReposWzUsername(username) {
        return apiClient.get(`/repos_config?username=${username}`)
    },
    getRepos(orgs) {
        const PromiseArr = [];
        for (let i = 0; i < orgs.length; i++) {
            var url = `/repos_config?org_name=${orgs[i]}`;
            PromiseArr.push(
                apiClient.get(url).then(result => new Promise(resolve => resolve(result.data)))
            );
        }
        return Promise.all(PromiseArr)
    },
    sendRepos(selectedRepos) {
        return apiClient.post('/repos_config', { repos: selectedRepos })
    },
    getTelegram() {
        return apiClient.get('/telegram_config')
    },
    setTelegramConfig(id, token) {
        return apiClient.post('/telegram_config', { chat_id: id, bot_token: token })
    },
    applyConfig() {
        return apiClient.post('/apply_config')
    }
}
