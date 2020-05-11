<template>
  <!--Begin::Section-->
  <div class="row">
    <Loading v-if="loading" />
    <div class="col-xl-8">
      <div class="row">
        <div class="col-xl-4 mb-3" v-for="repo in repos" :key="repo.id">
          <!--begin:: Widgets/Inbound Bandwidth-->
          <dashboard-repos :repo="repo"></dashboard-repos>
          <!--end:: Widgets/Inbound Bandwidth-->
        </div>
        <div class="kt-space-20"></div>
        <router-link
          :to="{name: 'ScheduleDetails', params: {name: schedule, id: id}}"
          class="col-xl-4 mb-3"
          v-for="schedule in schedules"
          :key="schedule.id"
        >
          <dashboard-schedules :schedule="schedule" @childToParent="getSelectedId"></dashboard-schedules>
        </router-link>
      </div>
    </div>

    <div class="col-xl-4">
      <!-- <support-ticket></support-ticket> -->
    </div>
  </div>

  <!--End::Section-->
</template>

<script>
import Loading from "./Loading";
import EventService from "../services/EventService";
import DashboardRepos from "./DashboardRepos";
import DashboardSchedules from "./DashboardSchedules";
import SupportTicket from "./SupportTicket";

export default {
  name: "Activity",
  components: {
    "dashboard-repos": DashboardRepos,
    "dashboard-schedules": DashboardSchedules,
    "support-ticket": SupportTicket,
    Loading: Loading
  },
  data() {
    return {
      loading: true,
      repos: null,
      schedules: null,
      id: null
    };
  },
  methods: {
    getData() {
      EventService.dashboardData()
        .then(response => {
          this.loading = false;
          this.repos = response.data.repos;
          this.schedules = response.data.schedules;
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
    this.getData();
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
