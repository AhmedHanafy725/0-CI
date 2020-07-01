<template>
  <!-- begin:: Content -->
  <div class="kt-portlet kt-portlet--mobile">
    <Loading v-if="loading" />
    <div class="kt-portlet__head kt-portlet__head--lg">
      <div class="kt-portlet__head-label">
        <span class="kt-portlet__head-icon">
          <i class="kt-font-brand flaticon2-line-chart"></i>
        </span>
        <h3 class="kt-portlet__head-title">{{ repoName }}/{{ branch }}</h3>
      </div>
      <div class="kt-header__topbar pr-0">
        <button
          type="button"
          class="btn btn-primary btn-sm text-white"
          :disabled="disabled"
          @click="restart()"
        >
          <i class="flaticon2-reload"></i> Restart build
        </button>
        <button
          type="button"
          class="kt-demo-icon mb-0"
          @click="runConfig()"
          data-toggle="modal"
          :data-target="'#kt_modal_' + model"
        >
          <i class="flaticon2-settings"></i>
        </button>
      </div>
    </div>
    <div class="kt-portlet__body">
      <v-card>
        <v-card-title>
          <!-- title -->
          <v-text-field
            v-model="search"
            append-icon="mdi-magnify"
            label="Search"
            single-line
            hide-details
          ></v-text-field>
        </v-card-title>
        <v-data-table :headers="headers" :items="details" :search="search">
          <template v-slot:item.id="{ item }">
            <router-link
              :to="'/repos/' + orgName + '/' + repoName + '/' + branch + '/' + item.id"
            >{{details.length - details.map(function(x) {return x.id; }).indexOf(item.id)}}</router-link>
          </template>

          <template v-slot:item.committer="{ item }">
            <div class="kt-user-card-v2">
              <div class="kt-user-card-v2__pic">
                <img
                  :src="committerSrc(item.committer)"
                  class="m-img-rounded kt-marginless"
                  alt="photo"
                />
              </div>
              <div class="kt-user-card-v2__details">
                <a
                  :href="committerUrl(item.committer)"
                  class="kt-user-card-v2__email kt-link"
                  target="_blank"
                >{{ item.committer }}</a>
              </div>
            </div>
          </template>

          <template v-slot:item.commit="{ item }">
            <a
              :href="repoCommit(item.commit)"
              class="kt-user-card-v2__email kt-link"
              target="_blank"
            >{{ commit(item.commit) }}</a>
          </template>

          <template v-slot:item.triggered_by="{ item }">
            <span>{{ item.triggered_by }}</span>
          </template>

          <template v-slot:item.bin_release="{ item }">
            <a
              :href="bin(item.bin_release)"
              class="kt-user-card-v2__email kt-link"
              target="_blank"
              v-if="item.bin_release !== null"
            >
              {{ commit(item.bin_release) }}
              <i class="la la-edit"></i>
            </a>
            <span v-else>-</span>
          </template>

          <template v-slot:item.status="{ item }">
            <v-chip :color="getStatus(item.status)" dark>{{ item.status }}</v-chip>
          </template>

          <template v-slot:item.timestamp="{ item }">
            <span>{{ time(item.timestamp) }}</span>
          </template>
        </v-data-table>
      </v-card>
    </div>
    <!--begin::Modal-->
    <div
      class="modal fade"
      id="kt_modal_4"
      tabindex="-1"
      role="dialog"
      aria-labelledby="exampleModalLabel"
      aria-hidden="true"
      v-if="newKeyModel"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exampleModalLabel">Environment Variables</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <!--begin::Form-->
            <span
              class="kt-spinner my-5 kt-spinner--v2 kt-spinner--lg kt-spinner--dark"
              v-if="formLoading"
            ></span>
            <!-- <div class="row" v-if="VarsValidate">
              <div class="offset-md-1 col">
                <div class="kt-section">
                  <div class="kt-section__info">{{ msg }}</div>
                </div>
              </div>
            </div>-->
            <form class="kt-form kt-form--label-right" @submit.prevent="addKey()">
              <div class="kt-portlet__body">
                <div class="form-group" v-if="keys">
                  <div class="row" v-for="(value, key, index) in keys" :key="index">
                    <div class="col align-self-center text-right">{{ index + 1}}.</div>
                    <div class="col-md-5">
                      <input class="form-control" type="text" :value="key" disabled />
                    </div>
                    <div class="col-md-5">
                      <input class="form-control" type="password" :value="value" disabled />
                    </div>
                    <div class="col align-self-center">
                      <i class="flaticon2-delete kt-font-error" @click="deleteKey(key, value)"></i>
                    </div>
                  </div>

                  <div class="row" v-if="fireInput">
                    <div class="offset-md-1 col-md-5">
                      <input
                        class="form-control"
                        type="text"
                        placeholder="Key"
                        v-model="newKey"
                        required
                      />
                    </div>
                    <div class="col-md-5">
                      <input
                        class="form-control"
                        type="text"
                        placeholder="Value"
                        v-model="newValue"
                        required
                      />
                    </div>
                  </div>

                  <div class="row">
                    <div class="offset-md-1 px-2">
                      <span class="kt-link" @click="fireInput = true, VarsValidate = false">
                        <i class="flaticon2-plus"></i>
                        Add new key
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="kt-portlet__foot text-right" v-if="fireInput">
                <div class="kt-form__actions">
                  <div class="row">
                    <div class="col">
                      <button type="submit" class="btn btn-success text-white">Add</button>
                      <button type="reset" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- end:: Content -->
</template>
<script>
import Loading from "../components/Loading";
import EventService from "../services/EventService";
import { orgs } from "../mixins/orgs";
export default {
  name: "BranchDetails",
  props: ["orgName", "repoName", "branch"],
  components: {
    Loading: Loading
  },
  mixins: [orgs],
  data() {
    return {
      search: "",
      model: "",
      headers: [
        { text: "#ID", value: "id" },
        { text: "Author", value: "committer" },
        { text: "Commit", value: "commit" },
        { text: "Triggered By", value: "triggered_by" },
        { text: "Bin", value: "bin_release" },
        { text: "Status", value: "status" },
        { text: "Time", value: "timestamp" }
      ],
      loading: true,
      details: [],
      newKeyModel: true,
      keys: null,
      fireInput: false,
      newKey: "",
      newValue: "",
      disabled: false,
      formLoading: true,
      VarsValidate: false,
      msg: "No Variables Existed"
    };
  },
  methods: {
    clear() {
      this.details = [];
    },
    reset() {
      this.newKey = "";
      this.newValue = "";
    },
    committerSrc(committer) {
      return (
        JSON.parse(window.localStorage.getItem("vcs")) +
        "/" +
        committer +
        ".png"
      );
    },
    committerUrl(committer) {
      return JSON.parse(window.localStorage.getItem("vcs")) + "/" + committer;
    },
    repoCommit(commit) {
      return (
        JSON.parse(window.localStorage.getItem("vcs")) +
        "/" +
        this.orgName +
        "/" +
        this.repoName +
        "/commit/" +
        commit
      );
    },
    bin(bin) {
      return `${window.location.origin}/bin/${this.orgName}/${this.repoName}/${this.branch}/${bin}`;
    },
    commit(commit) {
      return commit.substring(0, 7);
    },
    restart() {
      if (this.$store.state.user !== null) {
        EventService.restartBuild(this.fullRepoName, this.branch)
          .then(response => {
            this.loading = false;
            this.disabled = true;
          })
          .catch(error => {
            if (error.response.status == 503) {
              toastr.error(error.response.data);
            } else if (error.response.status == 401) {
              toastr.error("Please contact Adminstrator");
            } else {
              console.log("Error! Could not reach the API. " + error);
            }
          });
      } else {
        toastr.error("Please Login First!");
      }
    },
    runConfig() {
      if (
        this.$store.state.permission == "admin" ||
        this.$store.state.permission == "user"
      ) {
        this.model = 4;
        this.fireInput = false;
        EventService.runConfig(this.orgName + "/" + this.repoName)
          .then(response => {
            if (response) {
              this.formLoading = false;
              this.keys = response.data;
              if (response.data.length == undefined) {
                this.VarsValidate = true;
              }
            }
            if (this.keys == null) {
              this.VarsValidate = true;
            }
          })
          .catch(error => {
            console.log("Error! Could not reach the API. " + error);
          });
      } else if (this.$store.state.permission === "") {
        toastr.error("Please contact Adminstrator");
      } else {
        toastr.error("Please Login First!");
      }
    },
    addKey() {
      EventService.addKey(
        this.orgName + "/" + this.repoName,
        this.newKey,
        this.newValue
      )
        .then(response => {
          this.runConfig();
          this.fireInput = false;
          this.VarsValidate = false;
          this.reset();
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    deleteKey(key, value) {
      EventService.deleteKey(this.orgName + "/" + this.repoName, key, value)
        .then(response => {
          this.runConfig();
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    fetchData() {
      EventService.getBranchDetails(
        this.orgName + "/" + this.repoName,
        this.branch
      )
        .then(response => {
          this.loading = false;
          this.details = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    time(ts) {
      var timestamp = moment.unix(ts);
      var now = new Date();
      return timestamp.to(now);
    }
  },
  computed: {
    fullRepoName() {
      return this.orgName + "/" + this.repoName;
    }
  },
  mounted() {
    this.$options.sockets.onmessage = msg => {
      var data = JSON.parse(msg.data);

      let updated = this.details.find((o, i) => {
        if (o.id == data.id) {
          this.details[i].id = data.id;
          this.details[i].status = data.status;
          this.details[i].timestamp = data.timestamp;
          this.details[i].triggered_by = data.triggered_by;
          this.details[i].bin_release = data.bin_release;
          return true;
        }
      });
      if (updated == undefined) {
        this.details.unshift(data);
      }
    };
  },
  created() {
    this.fetchData();
  },
  watch: {
    "$route.params": {
      handler(newValue) {
        this.clear();
        this.loading = true;
        const { name } = newValue;
        this.fetchData();
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
.kt-spinner {
  margin: auto;
  display: table;
}

.kt-link,
.flaticon2-delete {
  cursor: pointer;
}

.v-card__title .v-input {
  max-width: 25%;
  margin-left: auto;
}
.kt-user-card-v2 .kt-user-card-v2__details .kt-user-card-v2__email {
  font-weight: 500;
}

.kt-portlet__head-icon {
  text-align: left;
}
</style>
