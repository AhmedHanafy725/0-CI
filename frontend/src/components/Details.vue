<template>
  <!-- begin:: Content -->
  <div class="kt-content kt-grid__item kt-grid__item--fluid" id="kt_content">
    <Loading v-if="loading" />
    <div class="kt-portlet kt-portlet--mobile">
      <div class="kt-portlet__head kt-portlet__head--lg">
        <div class="kt-portlet__head-label">
          <span class="kt-portlet__head-icon">
            <i class="kt-font-brand flaticon2-line-chart"></i>
          </span>
          <h3 class="kt-portlet__head-title">{{ repoName }}/{{ branch }}</h3>
        </div>

        <div class="kt-header__topbar pr-0">
          <button type="button" @click="viewLogs()" class="btn btn-primary btn-sm mr-1">View Logs</button>

          <button
            type="button"
            class="btn btn-primary btn-sm"
            :disabled="disabled"
            @click="rebuild()"
          >
            <i class="flaticon2-reload"></i> Restart build
          </button>
        </div>
      </div>
      <div class="kt-portlet__body">
        <!-- live logs -->
        <v-expansion-panels v-model="panel" v-if="live">
          <Live-Logs :livelogs="livelogs" />
        </v-expansion-panels>

        <!-- logs -->
        <v-expansion-panels>
          <logs v-for="log in logs" :key="log.id" :log="log" />
        </v-expansion-panels>
        <!-- testcases -->
        <v-expansion-panels>
          <test-suites
            v-for="testsuite in testsuites"
            :key="testsuite.id"
            :testsuite="testsuite"
            :index="testsuite.id"
          />
        </v-expansion-panels>
      </div>
    </div>
  </div>

  <!-- end:: Content -->
</template>

<script>
import EventService from "../services/EventService";
import LiveLogs from "./LiveLogs";
import Logs from "./Logs";
import TestSuites from "./TestSuites";
import Loading from "./Loading";
export default {
  name: "RepoDetails",
  props: ["orgName", "repoName", "branch", "id"],
  components: {
    "Live-Logs": LiveLogs,
    logs: Logs,
    Loading: Loading,
    "test-suites": TestSuites
  },
  data() {
    return {
      loading: true,
      live: false,
      panel: 0,
      logs: [],
      livelogs: [],
      testsuites: [],
      disabled: false
    };
  },
  methods: {
    connect() {
      this.socket = new WebSocket(
        "ws://" + window.location.hostname + `/websocket/logs/${this.id}`
      );
      this.socket.onopen = () => {
        this.socket.onmessage = ({ data }) => {
          this.livelogs.push(data);
        };
      };
    },
    fetchBrancheIdDetails() {
      EventService.getBranchIdDetails(
        this.orgName + "/" + this.repoName,
        this.branch,
        this.id
      )
        .then(response => {
          this.loading = false;
          response.data.map((job, index) => {
            if (job.type == "log") {
              this.logs.push(job);
            } else if (job.type == "testsuite") {
              this.testsuites.push(job);
            } else {
              this.viewLogs();
            }
          });
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    rebuild() {
      if (this.$store.state.user !== null) {
        this.loading = true;
        EventService.rebuildJob(this.id)
          .then(response => {
            if (response) {
              this.loading = false;
              this.disabled = true;
            }
          })
          .catch(error => {
            console.log("Error! Could not reach the API. " + error);
          });
      } else {
        toastr.error("Please Login First!");
      }
    },
    viewLogs() {
      this.panel = 1;
      this.live = !this.live;
      this.connect();
    }
  },
  created() {
    this.fetchBrancheIdDetails();
  }
};
</script>

<style scoped>
.v-expansion-panels {
  margin-bottom: 10px;
}
</style>
