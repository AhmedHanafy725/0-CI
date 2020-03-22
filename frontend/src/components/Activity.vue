<template>
  <!--Begin::Section-->
  <div class="row">
    <div
      class="kt-dialog kt-dialog--shown kt-dialog--default kt-dialog--loader kt-dialog--top-center"
      v-if="loading"
    >Loading ...</div>
    <div class="col-xl-8">
      <div class="row">
        <div class="col-xl-4 mb-3" v-for="(repo, index) in repos" :key="index + 'a'">
          <!--begin:: Widgets/Inbound Bandwidth-->
          <dashboard-repos :repo="repo"></dashboard-repos>
          <!--end:: Widgets/Inbound Bandwidth-->
        </div>
        <div class="kt-space-20"></div>
        <router-link
          :to="'/projects/' + project + '/' + id"
          class="col-xl-4 mb-3"
          v-for="(project, index) in projects"
          :key="index"
        >
          <dashboard-projects :project="project" @childToParent="getSelectedId"></dashboard-projects>
        </router-link>
      </div>
    </div>

    <div class="col-xl-4">
      <support-ticket></support-ticket>
    </div>
  </div>

  <!--End::Section-->
</template>

<script>
import axios from "axios";
import DashboardRepos from "./DashboardRepos";
import DashboardProjects from "./DashboardProjects";
import SupportTicket from "./SupportTicket";

export default {
  name: "Activity",
  components: {
    "dashboard-repos": DashboardRepos,
    "dashboard-projects": DashboardProjects,
    "support-ticket": SupportTicket
  },
  data() {
    return {
      loading: true,
      repos: null,
      projects: null,
      id: null
    };
  },
  methods: {
    latestAction() {
      const path = process.env.VUE_APP_BASE_URL;
      axios
        .get(path)
        .then(response => {
          this.repos = response.data.repos;
          this.projects = response.data.projects;
          this.loading = false;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    getSelectedId(value) {
      this.id = value;
    }
  },
  created() {
    this.latestAction();
  }
};
</script>

<style scoped>
@media (min-width: 1025px) {
  .kt-portlet.kt-portlet--height-fluid-half {
    height: 100%;
  }
}
</style>
