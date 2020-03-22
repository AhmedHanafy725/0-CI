import * as types from './mutation-types'

export const mutations = {
    [types.INIT_ORGS](state, payload) {
        state.repos = payload.repos
        state.projects = payload.projects
    }
}