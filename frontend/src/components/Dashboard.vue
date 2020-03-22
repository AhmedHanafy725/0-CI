<template>
  <div>
    <header-mobile></header-mobile>
    <main-page></main-page>
    <scroll-top></scroll-top>
  </div>
</template>

<script>
import HeaderMobile from "./HeaderMobile";
import MainContent from "./MainContent";
import ScrollTop from "./ScrollTop";
export default {
  name: "Dashboard",
  components: {
    "header-mobile": HeaderMobile,
    "main-page": MainContent,
    "scroll-top": ScrollTop
  }
};
</script>
