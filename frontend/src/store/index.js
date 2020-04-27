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
            localStorage.setItem('user', JSON.stringify(user))
        },
        SET_EMAIL(state, email) {
            state.email = email
            localStorage.setItem('email', JSON.stringify(email))
        },
        SET_PERMISSION(state, permission) {
            state.permission = permission
            localStorage.setItem('permission', JSON.stringify(permission))
        }
    },
    getters: {
        formatUser: state => {
            return state.user.replace('.3bot', ' ')
        }
    }
})
