import Vue from 'vue'
import Router from 'vue-router'
import Dashboard from '@/components/Dashboard'
import Main from '@/components/Main'
import BranchDetails from '@/components/BranchDetails'
import ProjectDetails from '@/components/ProjectDetails'
import Details from "@/components/Details"
import ProDetails from '@/components/ProDetails'
import UserLogin from '@/components/UserLogin'

Vue.use(Router)

export default new Router({
    mode: 'history',
    routes: [{
        path: '/',
        component: Main,
        redirect: '/dashboard',
        children: [{
                path: '/dashboard',
                name: 'Dashboard',
                component: Dashboard,
                meta: { breadcrumb: 'Dashboard' },
            },
            {
                path: '/auth/3bot_callback',
                name: 'Dashboard',
                component: Dashboard,
                props: true
            },
            {
                path: '/repos/:orgName/:repoName',
                name: 'BranchDetails',
                component: BranchDetails,
                meta: { param: ':orgName/:repoName' },
                props: true
            },
            {
                path: '/repos/:orgName/:repoName/:branch/:id',
                name: 'Details',
                component: Details,
                meta: { param: ':orgName/:repoName/:branch/:id' },
                props: true
            },
            {
                path: '/projects/:name',
                name: 'ProjectDetails',
                component: ProjectDetails,
                props: true
            },
            {
                path: '/projects/:name/:id',
                name: 'proDetails',
                component: ProDetails,
                props: true
            }
        ]
    }]
})
