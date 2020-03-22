import * as types from './mutation-types'
import Axios from 'axios'

export const initOrgs = ({ commit }) => {
    Axios
        .get(process.env.VUE_APP_BASE_URL)
        .then(response => commit(types.INIT_ORGS, response.data))
}