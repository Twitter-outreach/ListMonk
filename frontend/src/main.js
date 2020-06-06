import Vue from 'vue';
import Buefy from 'buefy';

import App from './App.vue';
import router from './router';
import store from './store';
import * as api from './api';
import utils from './utils';

Vue.use(Buefy, {});
Vue.config.productionTip = false;

// Custom global elements.
Vue.prototype.$api = api;
Vue.prototype.$utils = utils;

new Vue({
  router,
  store,
  render: (h) => h(App),
}).$mount('#app');
