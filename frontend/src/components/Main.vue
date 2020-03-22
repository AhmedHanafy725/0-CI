<template>
  <div style="background:#f2f3f8">
    <HeaderMobile />
    <div class="kt-grid kt-grid--hor kt-grid--root">
      <div class="kt-grid__item kt-grid__item--fluid kt-grid kt-grid--ver kt-page">
        <!-- begin:: Aside -->
        <SideBar />
        <!-- end:: Aside -->
        <div
          class="kt-grid__item kt-grid__item--fluid kt-grid kt-grid--hor kt-wrapper"
          id="kt_wrapper"
        >
          <!-- begin:: Header -->
          <header-menu></header-menu>
          <content-head></content-head>
          <!-- end:: Header -->
          <router-view></router-view>
          <!-- begin:: Footer -->
          <footer-sec></footer-sec>
          <!-- end:: Footer -->
        </div>
      </div>
      <!-- end:: Page -->
    </div>
  </div>
</template>

<script>
import HeaderMobile from "./HeaderMobile";
import SideBar from "./SideBar";
import Header from "./Header";
import FooterSec from "./Footer";
import ContentHead from "./ContentHead";
export default {
  name: "Main",
  components: {
    HeaderMobile,
    SideBar,
    "header-menu": Header,
    "footer-sec": FooterSec,
    "content-head": ContentHead
  }
};
</script>
