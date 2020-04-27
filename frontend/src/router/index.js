import Vue from 'vue'
import Router from 'vue-router'
import store from '../store/index'
import Login from '@/components/Login'
import Dashboard from '@/components/Dashboard'
import Main from '@/components/Main'
import BranchDetails from '@/components/BranchDetails'
import ProjectDetails from '@/components/ProjectDetails'
import Details from "@/components/Details"
import ProDetails from '@/components/ProDetails'
import InitialConfig from '@/components/InitialConfig'

Vue.use(Router)

const router = new Router({
    mode: 'history',
    routes: [{
            path: '/auth/login',
            name: 'Login',
            component: Login
        },
        {
            path: '/',
            component: Main,
            redirect: '/dashboard',
            children: [{
                    path: '/dashboard',
                    name: 'Dashboard',
                    component: Dashboard,
                    meta: { requiresAuth: true }
                },
                {
                    path: '/auth/3bot_callback',
                    name: 'Dashboard',
                    component: Dashboard,
                    props: true,
                    beforeEnter(to, from, next) {
                        let str = JSON.parse(to.query.signedAttempt);
                        store.commit('SET_USER', str.doubleName)
                        store.commit('SET_TOKEN', str.signedAttempt)
                        next('/')
                    },
                },
                {
                    path: '/repos/:orgName/:repoName',
                    name: 'BranchDetails',
                    component: BranchDetails,
                    props: true
                },
                {
                    path: '/repos/:orgName/:repoName/:branch/:id',
                    name: 'Details',
                    component: Details,
                    props: true
                },
                {
                    path: '/schedules/:name',
                    name: 'ProjectDetails',
                    component: ProjectDetails,
                    props: true
                },
                {
                    path: '/schedules/:name/:id',
                    name: 'ScheduleDetails',
                    component: ProDetails,
                    props: true
                },
                {
                    path: '/initial_config',
                    name: 'InitialConfig',
                    component: InitialConfig
                }
            ]
        }
    ]
})

// router.beforeEach((to, from, next) => {
//     if (to.matched.some(record => record.meta.requiresAuth) && (!store.state.token || store.state.token === 'null')) {
//         next({
//             name: 'Login'
//         })
//     } else {
//         next()
//     }
// })

export default router
