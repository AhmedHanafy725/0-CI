import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
    state: {
        user: null,
        token: null
    },
    mutations: {
        SET_USER(state, user) {
            state.user = user
            localStorage.setItem('user', JSON.stringify(user))
        },
        SET_TOKEN(state, token) {
            state.token = token
            localStorage.setItem("token", token);
        }
    },
    getters: {
        formatUser: state => {
            return state.user.replace('.3bot', ' ')
        }
    }
})
