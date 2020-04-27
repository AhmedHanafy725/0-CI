import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
    state: {
        user: null,
        email: null,
        permission: null
    },
    mutations: {
        SET_USER(state, user) {
            state.user = user
        },
        SET_EMAIL(state, email) {
            state.email = email
        },
        SET_PERMISSION(state, permission) {
            state.permission = permission
        }
    },
    getters: {
        formatUser: state => {
            return state.user.replace('.3bot', ' ')
        }
    }
})
