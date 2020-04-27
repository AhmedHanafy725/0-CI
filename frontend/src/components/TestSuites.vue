<template>
  <v-expansion-panel>
    <v-expansion-panel-header>
      <span class="kt-portlet__head-icon">
        <i class="kt-font-brand" :class="getStatus(testsuite.status)"></i>
        {{ testsuite.name }}
      </span>
    </v-expansion-panel-header>
    <v-expansion-panel-content>
      <v-tabs v-model="tab">
        <v-tab :href="'#all-' + index">
          <v-badge color="grey" :content="summary.tests">All</v-badge>
        </v-tab>
        <v-tab :href="'#errored-' + index">
          <v-badge color="red" :content="summary.errors">Errored</v-badge>
        </v-tab>
        <v-tab :href="'#failed-' + index">
          <v-badge color="red" :content="summary.failures">Failed</v-badge>
        </v-tab>
        <v-tab :href="'#skipped-' + index">
          <v-badge color="orange" :content="summary.skip">Skipped</v-badge>
        </v-tab>
      </v-tabs>

      <v-tabs-items v-model="tab">
        <v-tab-item :id="'all-' + index">
          <v-card flat>
            <v-card-text>
              <v-expansion-panels>
                <v-expansion-panel v-for="testcase in testcases" :key="testcase.id">
                  <v-expansion-panel-header>
                    <span class="kt-portlet__head-icon">
                      <i class="kt-font-brand" :class="getStatus(testcase.status)"></i>
                      {{ testcase.classname }} {{ testcase.name }}
                    </span>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content
                    class="v-card v-card--flat v-sheet v-sheet--tile theme--dark"
                  >
                    <pre class="white--text"><code>{{ testcase.status }} &nbsp; (Executed in {{ testcase.time }} seconds)</code>
                            <code v-if="testcase.details">{{ testcase.details.content }}<br />{{ testcase.details.message }}</code></pre>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-card-text>
          </v-card>
        </v-tab-item>

        <v-tab-item :id="'errored-' + index">
          <v-card flat>
            <v-card-text>
              <v-expansion-panels>
                <v-expansion-panel v-for="error in errors" :key="error.id">
                  <v-expansion-panel-header>
                    <span class="kt-portlet__head-icon">
                      <i class="kt-font-brand" :class="getStatus(error.status)"></i>
                      {{ error.classname }} {{ error.name }}
                    </span>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content
                    class="v-card v-card--flat v-sheet v-sheet--tile theme--dark"
                  >
                    <pre class="white--text"><code>{{ error.status }} &nbsp; (Executed in {{ error.time }} seconds)</code>
                            <code v-if="error.details">{{ error.details.content }}<br />{{ error.details.message }}</code></pre>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-card-text>
          </v-card>
        </v-tab-item>

        <v-tab-item :id="'failed-' + index">
          <v-card flat>
            <v-card-text>
              <v-expansion-panels>
                <v-expansion-panel v-for="failure in failures" :key="failure.id">
                  <v-expansion-panel-header>
                    <span class="kt-portlet__head-icon">
                      <i class="kt-font-brand" :class="getStatus(failure.status)"></i>
                      {{ failure.classname }} {{ failure.name }}
                    </span>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content
                    class="v-card v-card--flat v-sheet v-sheet--tile theme--dark"
                  >
                    <pre class="white--text"><code>{{ failure.status }} &nbsp; (Executed in {{ failure.time }} seconds)</code>
                            <code v-if="failure.details">{{ failure.details.content }}<br />{{ failure.details.message }}</code></pre>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-card-text>
          </v-card>
        </v-tab-item>

        <v-tab-item :id="'skipped-' + index">
          <v-card flat>
            <v-card-text>
              <v-expansion-panels>
                <v-expansion-panel v-for="skip in skips" :key="skip.id">
                  <v-expansion-panel-header>
                    <span class="kt-portlet__head-icon">
                      <i class="kt-font-brand" :class="getStatus(skip.status)"></i>
                      {{ skip.classname }} {{ skip.name }}
                    </span>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content
                    class="v-card v-card--flat v-sheet v-sheet--tile theme--dark"
                  >
                    <pre class="white--text"><code>{{ skip.status }} &nbsp; (Executed in {{ skip.time }} seconds)</code>
                            <code v-if="skip.details">{{ skip.details.content }}<br />{{skip.details.message }}</code></pre>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-card-text>
          </v-card>
        </v-tab-item>
      </v-tabs-items>
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>

<script>
import AnsiUp from "ansi_up";

export default {
  name: "TestSuites",
  props: ["testsuite", "index"],
  data() {
    return {
      tab: null,
      summary: this.testsuite.content.summary,
      testcases: this.testsuite.content.testcases,
      all: [],
      errors: [],
      failures: [],
      skips: [],
      ansi: undefined
    };
  },
  methods: {
    mapData() {
      this.testcases.map((testcase, index) => {
        if (testcase.status == "errored") {
          this.errors.push(testcase);
        } else if (testcase.status == "failed") {
          this.failures.push(testcase);
        } else if (testcase.status == "skipped") {
          this.skips.push(testcase);
        }
      });
    },
    getStatus(status) {
      if (status == "error" || status == "errored")
        return "kt-font-error flaticon-exclamation-1";
      else if (status == "failure" || status == "failed")
        return "kt-font-failure flaticon2-delete";
      else if (status == "success" || status == "passed")
        return "kt-font-success flaticon2-checkmark";
      else if (status == "skipped")
        return "kt-font-warning flaticon-warning-sign";
    },
    html(content) {
      // Ensures we have some semblance of lines
      return this.ansi.ansi_to_html(content);
    }
  },
  created() {
    this.ansi = new AnsiUp();
    this.mapData();
  }
};
</script>
