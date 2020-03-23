<template>
  <!-- begin:: Content -->
  <div class="kt-content kt-grid__item kt-grid__item--fluid" id="kt_content">
    <div class="kt-portlet kt-portlet--mobile">
      <div class="kt-portlet__head kt-portlet__head--lg">
        <div class="kt-portlet__head-label">
          <span class="kt-portlet__head-icon">
            <i class="kt-font-brand flaticon2-line-chart"></i>
          </span>
          <h3 class="kt-portlet__head-title">{{ repoName }}/{{ branch }}</h3>
        </div>
        <button type="button" class="btn btn-primary btn-sm" @click="rebuild()">
          <i class="flaticon2-reload"></i> Restart job
        </button>
      </div>
      <div class="kt-portlet__body">
        <!-- logs -->
        <v-expansion-panels>
          <logs v-for="(log,i) in logs" :key="i" :log="log"></logs>
        </v-expansion-panels>
        <!-- testcases -->
        <v-expansion-panels>
          <test-suites
            v-for="(testsuite, index) in testsuites"
            :key="index"
            :testsuite="testsuite"
            :index="index"
            :testcases="testcases"
            :summary="summary"
          ></test-suites>
        </v-expansion-panels>
      </div>
    </div>
  </div>

  <!-- end:: Content -->
</template>

<script>
import axios from "axios";
import Logs from "./Logs";
import TestSuites from "./TestSuites";

export default {
  name: "RepoDetails",
  props: ["orgName", "repoName", "branch", "id"],
  components: {
    logs: Logs,
    "test-suites": TestSuites
  },
  data() {
    return {
      data: null,
      testsuites: [],
      summary: [],
      testcases: null,
      logs: []
    };
  },
  methods: {
    getDetails() {
      const path =
        process.env.VUE_APP_BASE_URL +
        `repos/${this.orgName}/${this.repoName}?branch=${this.branch}&&id=${this.id}`;
      axios
        .get(path)
        .then(response => {
          this.data = response.data;
          this.data.map((job, index) => {
            if (job.type == "log") {
              this.logs.push(job);
            } else if (job.type == "testsuite") {
              this.testsuites.push(job);
              this.summary.push(job.content.summary);
              this.testcases = job.content.testcases;
            }
          });
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    rebuild() {
      const path = process.env.VUE_APP_BASE_URL + "run_trigger";
      axios
        .post(
          path,
          { id: this.id }, //repo, branch
          {
            headers: {
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "*"
            }
          }
        )
        .then(response => {
          console.log(response);
        })
        .catch(error => {
                    console.log(this.id)

          console.log("Error! Could not reach the API. " + error);
        });
    }
  },

  created() {
    this.getDetails();
  }
};
</script>
