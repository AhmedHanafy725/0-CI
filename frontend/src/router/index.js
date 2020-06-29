import Vue from 'vue'
import Router from 'vue-router'
import store from '../store'
import EventService from '@/services/EventService'
import Content from '@/components/Content'
import Dashboard from "@/views/Dashboard";
import BranchDetails from "@/views/BranchDetails";
import Details from "@/views/Details";
import Schedules from "@/views/Schedules";
import SchedulesDetails from "@/views/SchedulesDetails";
import InitialConfig from '@/views/InitialConfig'

Vue.use(Router)

const router = new Router({
    mode: 'history',
    routes: [{
            path: '/initial_config',
            name: 'InitialConfig',
            component: InitialConfig,
            meta: { layout: "Config" },
            beforeEnter(to, from, next) {
                if (store.state.permission == 'admin') {
                    next()
                } else if (store.state.user == null) {
                    next('/')
                }
            }
        },
        {
            path: '/',
            component: Content,
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
                    name: 'Schedules',
                    component: Schedules,
                    props: true
                },
                {
                    path: '/schedules/:name/:id',
                    name: 'ScheduleDetails',
                    component: SchedulesDetails,
                    props: true
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