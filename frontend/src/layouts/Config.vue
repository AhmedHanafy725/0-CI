<template>
  <div id="app">
    <v-app>
      <v-content class="config">
        <router-view />
      </v-content>
    </v-app>
  </div>
</template>

<script>
export default {
  name: "config"
};
</script>

<style scoped>
.config {
  background-image: url("/static/assets/media/bg/bg-2.jpg");
}
</style>
