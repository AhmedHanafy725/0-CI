<template>
  <!-- begin:: Content -->
  <div class="kt-portlet kt-portlet--mobile">
    <Loading v-if="loading" />
    <div class="kt-portlet__head kt-portlet__head--lg">
      <div class="kt-portlet__head-label">
        <span class="kt-portlet__head-icon">
          <i class="kt-font-brand flaticon2-line-chart"></i>
        </span>
        <h3 class="kt-portlet__head-title">{{ name }}</h3>
      </div>
      <div class="kt-header__topbar pr-0">
        <button type="button" @click="viewLogs()" class="btn btn-primary btn-sm mr-1">{{ result }}</button>
      </div>
    </div>
    <div class="kt-portlet__body">
      <!-- live logs -->
      <v-expansion-panels v-model="panel" v-if="live && livelogs.length > 0">
        <Live-Logs :livelogs="livelogs" />
      </v-expansion-panels>
      <!-- logs -->
      <v-expansion-panels v-model="panel" v-if="!live">
        <logs v-for="log in logs" :key="log.id" :log="log"></logs>
      </v-expansion-panels>

      <!-- testcases -->
      <v-expansion-panels v-model="panel" v-if="!live">
        <test-suites v-for="testsuite in testsuites" :key="testsuite.id" :testsuite="testsuite"></test-suites>
      </v-expansion-panels>
    </div>
  </div>

  <!-- end:: Content -->
</template>

<script>
import EventService from "../services/EventService";
import LiveLogs from "../components/LiveLogs";
import Logs from "../components/Logs";
import TestSuites from "../components/TestSuites";
import Loading from "../components/Loading";

export default {
  name: "ProDetails",
  props: ["name", "id"],
  components: {
    logs: Logs,
    "test-suites": TestSuites,
    Loading: Loading,
    "Live-Logs": LiveLogs
  },
  data() {
    return {
      disabled: false,
      testsuites: [],
      logs: [],
      loading: true,
      panel: 0,
      livelogs: [],
      result: "View logs",
      live: false
    };
  },
  methods: {
    getDetails() {
      EventService.getProjectIdDetails(this.name, this.id)
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
    viewLogs() {
      this.live = !this.live;
      if (this.live) {
        this.result = "View Result";
        this.connect();
      } else {
        this.result = "View Logs";
      }
    },
    connect() {
      this.socket = new WebSocket(
        "ws://" + window.location.hostname + `/websocket/logs/${this.id}`
      );
      this.socket.onmessage = ({ data }) => {
        this.livelogs = data;
      };
    }
  },
  created() {
    this.getDetails();
  }
};
</script>
