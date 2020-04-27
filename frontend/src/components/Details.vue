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
        <button
          type="button"
          class="btn btn-primary btn-sm"
          :disabled="disabled"
          @click="rebuild()"
        >
          <i class="flaticon2-reload"></i> Restart job
        </button>
      </div>
      <div class="kt-portlet__body">
        <!-- logs -->
        <v-expansion-panels>
          <logs v-for="log in logs" :key="log.id" :log="log"></logs>
        </v-expansion-panels>
        <!-- testcases -->
        <v-expansion-panels>
          <test-suites
            v-for="testsuite in testsuites"
            :key="testsuite.id"
            :testsuite="testsuite"
            :index="testsuite.id"
          ></test-suites>
        </v-expansion-panels>
      </div>
    </div>
  </div>

  <!-- end:: Content -->
</template>

<script>
import EventService from "../services/EventService";
import Logs from "./Logs";
import TestSuites from "./TestSuites";
import Loading from "./Loading";
export default {
  name: "RepoDetails",
  props: ["orgName", "repoName", "branch", "id"],
  components: {
    logs: Logs,
    Loading: Loading,
    "test-suites": TestSuites
  },
  data() {
    return {
      loading: true,
      logs: [],
      testsuites: [],
      disabled: false
    };
  },
  methods: {
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
            }
          });
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    rebuild() {
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
    }
  },
  created() {
    this.fetchBrancheIdDetails();
  }
};
</script>
