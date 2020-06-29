<template>
  <div id="app">
    <Header-Mobile />
    <Main-Sec />
    <Scroll-Btn />
  </div>
</template>

<script>
import HeaderMobile from "../components/HeaderMobile";
import Main from "../components/Main";
import Scroll from "../components/Scroll";

export default {
  name: "default",
  components: {
    "Header-Mobile": HeaderMobile,
    "Main-Sec": Main,
    "Scroll-Btn": Scroll
  }
};
</script>
