<template>
  <div>
    <!-- begin:: Aside -->
    <button class="kt-aside-close" id="kt_aside_close_btn">
      <i class="la la-close"></i>
    </button>
    <div
      class="kt-aside kt-aside--fixed kt-grid__item kt-grid kt-grid--desktop kt-grid--hor-desktop"
      id="kt_aside"
    >
      <!-- begin:: Aside -->
      <Aside />
      <!-- end:: Aside -->

      <!-- begin:: Aside Menu -->
      <AsideMenu />
      <!-- end:: Aside Menu -->
    </div>

    <!-- end:: Aside -->
  </div>
</template>

<script>
import Aside from "./Aside";
import AsideMenu from "./AsideMenu";
export default {
  name: "SideBar",
  components: {
    Aside,
    AsideMenu
  }
};
</script>

