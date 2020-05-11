import Vue from 'vue'
import Router from 'vue-router'
import store from '../store/index'
import Dashboard from '@/components/Dashboard'
import Main from '@/components/Main'
import BranchDetails from '@/components/BranchDetails'
import ProjectDetails from '@/components/ProjectDetails'
import Details from "@/components/Details"
import ProDetails from '@/components/ProDetails'
import InitialConfig from '@/components/InitialConfig'
import EventService from '@/services/EventService'
import NotFound from '@/components/404.vue';

Vue.use(Router)

const router = new Router({
    mode: 'history',
    routes: [{
            path: '/initial_config',
            name: 'InitialConfig',
            component: InitialConfig,
            beforeEnter(to, from, next) {
                if (store.state.user == null) {
                    next('/')
                }
            }
        },
        {
            path: '/',
            component: Main,
            redirect: '/dashboard',
            children: [{
                    path: '/dashboard',
                    name: 'Dashboard',
                    component: Dashboard
                },
                {
                    path: '/repos/:orgName/:repoName/:branch',
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
                    path: '/404',
                    name: '404',
                    component: NotFound
                },
                // {
                //     path: '*',
                //     redirect: '/404'
                // }
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