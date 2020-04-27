import Vue from 'vue'
import Router from 'vue-router'
import store from '../store/index'
import Login from '@/components/LoginPage'
import Dashboard from '@/components/Dashboard'
import Main from '@/components/Main'
import BranchDetails from '@/components/BranchDetails'
import ProjectDetails from '@/components/ProjectDetails'
import Details from "@/components/Details"
import ProDetails from '@/components/ProDetails'
import InitialConfig from '@/components/InitialConfig'
import EventService from '@/services/EventService'

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

router.beforeEach((to, from, next) => {
    // ${to and from are Route Object,next() must be called to resolve the hook}
    EventService.auth().then(response => {
            store.commit('SET_USER', response.data.username)
            store.commit('SET_EMAIL', response.data.email)
            store.commit('SET_PERMISSION', response.data.permission)
            next()
        })
        .catch(error => {
            if (error.response.status == 403) {
                store.commit('SET_USER', null)
                next()
            }
        });
})

export default router
