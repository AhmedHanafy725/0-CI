<template>
  <v-expansion-panel>
    <v-expansion-panel-header>
      <span class="kt-portlet__head-icon">
        <i class="kt-font-brand"></i>
        <span class="kt-badge kt-bg-error kt-badge--inline kt-badge--pill kt-badge--rounded">Live</span> Logs
      </span>
    </v-expansion-panel-header>
    <v-expansion-panel-content class="v-card v-card--flat v-sheet v-sheet--tile theme--dark">
      <pre><code v-for="livelog in livelogs" :key="livelog.id">{{ livelog }}</code></pre>
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>

<script>
export default {
  name: "LiveLogs",
  props: ["livelogs"]
};
</script>

<style scoped>
.v-card {
  max-height: 500px;
  overflow: auto;
  display: flex;
  flex-direction: column-reverse;
}
code {
  box-shadow: none;
}

.kt-portlet .kt-portlet__body {
  overflow: hidden;
}

.kt-bg-error {
  font-weight: bold;
}
</style>
