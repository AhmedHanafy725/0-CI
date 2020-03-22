<template>
  <v-expansion-panel>
    <v-expansion-panel-header>
      <span class="kt-portlet__head-icon">
        <i class="kt-font-brand" :class="getStatus(log.status)"></i>
        {{ log.name }}
      </span>
    </v-expansion-panel-header>
    <v-expansion-panel-content class="v-card v-card--flat v-sheet v-sheet--tile theme--dark">
      <pre><code v-html="html(log.content)"></code></pre>
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>

<script>
import AnsiUp from "ansi_up";

export default {
  name: "Logs",
  props: ["log"],
  data() {
    return {
      ansi: undefined
    };
  },
  methods: {
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
  }
};
</script>
