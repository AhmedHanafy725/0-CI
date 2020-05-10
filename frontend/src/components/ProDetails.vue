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
          <h3 class="kt-portlet__head-title">{{ name }}</h3>
        </div>
      </div>
      <div class="kt-portlet__body">
        <!-- live logs -->
        <v-expansion-panels v-model="panel" v-if="livelogs > 0">
          <Live-Logs :livelogs="livelogs" />
        </v-expansion-panels>
        <!-- logs -->
        <v-expansion-panels>
          <logs v-for="log in logs" :key="log.id" :log="log"></logs>
        </v-expansion-panels>

        <!-- testcases -->
        <v-expansion-panels>
          <test-suites v-for="testsuite in testsuites" :key="testsuite.id" :testsuite="testsuite"></test-suites>
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
      livelogs: []
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
            }
          });
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    connect() {
      this.socket = new WebSocket(
        "ws://" + window.location.hostname + `/websocket/logs/${this.id}`
      );
      this.socket.onopen = () => {
        this.socket.onmessage = ({ data }) => {
          this.livelogs.push(data);
        };
      };
    }
  },
  created() {
    this.connect();
    this.getDetails();
  }
};
</script>
