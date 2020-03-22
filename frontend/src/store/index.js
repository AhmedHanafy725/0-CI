import Vue from 'vue'
import Vuex from 'vuex'
import { mutations } from './mutation'
import * as actions from './actions'

Vue.use(Vuex)

const state = {
    repos: null,
    projects: null,
}

export default new Vuex.Store({
    state,
    mutations,
    actions
})