<template>
  <!-- begin:: Header Mobile -->
  <div id="kt_header_mobile" class="kt-header-mobile kt-header-mobile--fixed">
    <div class="kt-header-mobile__logo">
      <a :href="link">
        <img alt="Logo" :src="img" width="92"/>
      </a>
    </div>
    <div class="kt-header-mobile__toolbar">
      <button
        class="kt-header-mobile__toggler kt-header-mobile__toggler--left"
        id="kt_aside_mobile_toggler"
      >
        <span></span>
      </button>
      <button class="kt-header-mobile__toggler" id="kt_header_mobile_toggler">
        <span></span>
      </button>
      <button class="kt-header-mobile__topbar-toggler" id="kt_header_mobile_topbar_toggler">
        <i class="flaticon-more"></i>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "HeaderMobile",
  data() {
    return {
      link: "/",
      img: "/src/assets/media/logos/logo-light.png"
    };
  }
};
</script>
