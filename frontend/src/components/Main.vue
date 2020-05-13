<template>
  <div class="kt-grid kt-grid--hor kt-grid--root">
    <div class="kt-grid__item kt-grid__item--fluid kt-grid kt-grid--ver kt-page">
      <!-- begin:: Aside -->
      <button class="kt-aside-close" id="kt_aside_close_btn">
        <i class="la la-close"></i>
      </button>
      <Side-Bar />
      <Content-Wrapper />
    </div>
  </div>
</template>

<script>
import Sidebar from "./Sidebar";
import ContentWrapper from "./ContentWrapper";
export default {
  name: "Main",
  components: {
    "Side-Bar": Sidebar,
    "Content-Wrapper": ContentWrapper
  }
};
</script>
