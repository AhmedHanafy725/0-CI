<template>
  <div id="app">
    <v-app>
      <v-content>
        <Header-Mobile />
        <Main-Sec />
        <Scroll-Btn />
      </v-content>
    </v-app>
  </div>
</template>

<script>
import HeaderMobile from "./components/HeaderMobile";
import Main from "./components/Main";
import Scroll from "./components/Scroll";
export default {
  name: "App",
  components: {
    "Header-Mobile": HeaderMobile,
    "Main-Sec": Main,
    "Scroll-Btn": Scroll
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
