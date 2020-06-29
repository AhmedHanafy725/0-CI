<template>
  <div id="app">
    <v-app>
      <v-content>
        <component :is="layout">
          <router-view />
        </component>
      </v-content>
    </v-app>
  </div>
</template>

<script>
const default_layout = "Default";
export default {
  name: "App",

  computed: {
    layout() {
      return (this.$route.meta.layout || default_layout) + "-Layout";
    }
  },
  mounted: function() {
    let elHtml = document.getElementsByTagName("html")[0];
    elHtml.style.overflowY = "auto";
  },
  destroyed: function() {
    let elHtml = document.getElementsByTagName("html")[0];
    elHtml.style.overflowY = null;
  }
};
</script>
