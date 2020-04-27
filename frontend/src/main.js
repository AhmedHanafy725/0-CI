// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import 'vuetify/dist/vuetify.min.css'
import Vue from 'vue'
import App from './App'
import router from './router'
import store from './store/index'
import vuetify from './plugins/vuetify'
import upperFirst from 'lodash/upperFirst'
import camelCase from 'lodash/camelCase'


// var ws = new WebSocket("ws://localhost:8000/websocket/repos/AhmedHanafy725/test_zeroci/development");

// ws.onmessage = function(evt) {
//     console.log(evt.data);
// };

const requireComponent = require.context(
    // The relative path of the components folder
    './components',
    // Whether or not to look in subfolders
    false,
    // The regular expression used to match base component filenames
    /Base[A-Z]\w+\.(vue|js)$/
)

requireComponent.keys().forEach(fileName => {
    // Get component config
    const componentConfig = requireComponent(fileName)

    // Get PascalCase name of component
    const componentName = upperFirst(
        camelCase(
            // Gets the file name regardless of folder depth
            fileName
            .split('/')
            .pop()
            .replace(/\.\w+$/, '')
        )
    )

    // Register component globally
    Vue.component(
        componentName,
        // Look for the component options on `.default`, which will
        // exist if the component was exported with `export default`,
        // otherwise fall back to module's root.
        componentConfig.default || componentConfig
    )
})

// Check local storage to handle refreshes
if (localStorage) {
    var localUserString = localStorage.getItem('user') || 'null'
    var localUser = JSON.parse(localUserString)

    if (localUser && store.state.user !== localUser) {
        store.commit('SET_USER', localUser)
        store.commit('SET_TOKEN', localStorage.getItem('token'))
    }
}

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
    el: '#app',
    router,
    store,
    components: { App },
    vuetify,
    template: '<App/>'
})
