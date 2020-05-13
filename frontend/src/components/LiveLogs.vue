<template>
  <v-expansion-panel>
    <v-expansion-panel-header>
      <span class="kt-portlet__head-icon text-left">
        <i class="kt-font-brand"></i>
        <span class="kt-badge kt-bg-success kt-badge--inline kt-badge--pill kt-badge--rounded">Live</span> Logs
      </span>
    </v-expansion-panel-header>
    <v-expansion-panel-content
      id="console"
      class="v-card v-card--flat v-sheet v-sheet--tile theme--dark"
    >
      <pre><code v-html="html"></code></pre>
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>

<script>
import AnsiUp from "ansi_up";

export default {
  name: "LiveLogs",
  props: ["livelogs"],
  data() {
    return {
      ansi: undefined
    };
  },
  computed: {
    html() {
      // Ensures we have some semblance of lines
      return this.ansi.ansi_to_html(this.livelogs);
    }
  },
  beforeMount() {
    this.ansi = new AnsiUp();
  },
  updated() {
    var el = document.getElementById("console");
    el.scrollTop = el.scrollHeight;
    console.log(this.livelogs);
  }
};
</script>

<style scoped>
.v-card {
  max-height: 500px;
  font-family: monospace;
  overflow-y: auto;
}
code {
  box-shadow: none;
}

.kt-portlet .kt-portlet__body {
  overflow: hidden;
}

.kt-bg-success {
  font-weight: bold;
}
</style>
