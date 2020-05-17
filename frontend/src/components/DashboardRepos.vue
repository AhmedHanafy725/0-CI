<template>
  <div
    class="kt-portlet kt-portlet--fit kt-portlet--head-noborder kt-portlet--height-fluid-half mb-0"
  >
    <div class="kt-portlet__head kt-portlet__space-x">
      <div class="kt-portlet__head-label">
        <h3 class="kt-portlet__head-title">{{ repo | removeOrg }}</h3>
      </div>
      <branch-Dropdown :repo="repo" @childToParent="getSelectedBranch" />
    </div>
    <div class="kt-widget24__details kt-portlet__space-x">
      <i class="fa fa-code-branch"></i>
      <span class="kt-widget24__desc">{{ default_branch }}</span>
    </div>
    <div class="kt-portlet__body kt-portlet__body--fluid pt-0">
      <div class="kt-widget20">
        <div class="kt-widget20__content kt-portlet__space-x">
          <router-link :to="'/repos/' + repo + '/' + default_branch + '/' + id">
            <span
              class="kt-widget20__number text-capitalize"
              :class="{
            'kt-font-success': status == 'success',
            'kt-font-error': status == 'error',
            'kt-font-failure': status == 'failure'}"
            >{{ status }}</span>
          </router-link>

          <div class="kt-list-pics kt-list-pics--sm">
            <a :href="committerUrl" target="_blank">
              <img :src="committerSrc" title />
              <span class="kt-widget20__desc">{{ committer }}</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BranchDropdown from "./BranchDropdown";
import EventService from "../services/EventService";
export default {
  name: "DashboardRepos",
  props: ["repo"],
  components: {
    "branch-Dropdown": BranchDropdown
  },
  data() {
    return {
      default_branch: "master",
      branchData: null,
      committer: null,
      timestamp: null,
      status: null,
      id: null,
      filteredItems: []
    };
  },
  filters: {
    removeOrg(value) {
      return value.substring(value.indexOf("/") + 1);
    }
  },
  methods: {
    fetchDetails() {
      return EventService.getBranchDetails(this.repo, this.default_branch)
        .then(response => {
          this.branchData = response.data;
          if (this.branchData.length > 0) {
            this.committer = response.data[0].committer;
            this.timestamp = response.data[0].timestamp;
            this.status = response.data[0].status;
            this.id = response.data[0].id;
          } else {
            this.clear();
          }
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    getSelectedBranch(value) {
      this.default_branch = value;
      this.fetchDetails();
    },

    clear() {
      this.committer = null;
      this.timestamp = null;
      this.status = null;
      this.id = null;
    }
  },
  computed: {
    committerSrc() {
      return `http://github.com/${this.committer}.png`;
    },
    committerUrl() {
      return `http://github.com/${this.committer}`;
    }
  },
  created() {
    this.fetchDetails();
  },
  mounted() {
    this.$options.sockets.onmessage = msg => {
      var data = JSON.parse(msg.data);
      this.committer = data.committer;
      this.timestamp = data.timestamp;
      this.status = data.status;
      this.id = data.id;
    };
  }
};
</script>

<style scoped>
.kt-widget20__content a {
  margin-bottom: 10px;
}
</style>
