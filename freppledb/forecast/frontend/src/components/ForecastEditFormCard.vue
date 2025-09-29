/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

<script setup lang="js">
import {useForecastsStore} from "@/stores/forecastsStore.js";

const store = useForecastsStore();
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title text-capitalize mb-0" data-translate=""><span class="ng-scope">edit</span></h5>
    </div>
    <div class="card-body">
      <table>
        <tbody><tr>
          <td style="vertical-align:top; padding: 15px">
            <button id="applyedit" type="submit" data-ng-click="applyEdit()" class="btn btn-primary disabled" translate=""><span class="ng-scope">Apply</span></button>
          </td>
          <td><form class="mb-3 ng-pristine ng-valid">
            Update
            <div class="dropdown" style="display:inline-block">
              <button type="button" class="dropdown-toggle form-control d-inline w-auto ng-binding" data-bs-toggle="dropdown" id="editmeasure" name="editmeasure" aria-haspopup="true" aria-expanded="true" style="min-width:200px">
                forecast override&nbsp;&nbsp;<span class="caret"></span>
              </button>
              <ul class="dropdown-menu" aria-labelledby="editmeasure">
                <!-- ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">forecast override</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">forecast override value</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">no data</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment 1 years ago</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment 2 years ago</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment 3 years ago</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment value</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment value 1 years ago</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment value 2 years ago</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><li data-ng-repeat="m in measurelist | orderBy:'label'" data-ng-if="m.editable" class="ng-scope">
                <a class="dropdown-item" data-ng-click="$parent.$parent.edit_measure = m.name; changeEdit()" href="#" translate=""><span class="ng-binding ng-scope">orders adjustment value 3 years ago</span></a>
              </li><!-- end ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' --><!-- ngIf: m.editable --><!-- end ngRepeat: m in measurelist | orderBy:'label' -->
              </ul>
            </div>
            &nbsp;from&nbsp;
            <input id="editstartdate" type="date" class="form-control d-inline w-auto ng-pristine ng-untouched ng-valid ng-not-empty" data-ng-model="edit_startdate" data-ng-change="changeEdit()" style="background: white !important">
            &nbsp;till&nbsp;
            <input id="editenddate" type="date" class="form-control d-inline w-auto ng-pristine ng-untouched ng-valid ng-not-empty" data-ng-model="edit_enddate" data-ng-change="changeEdit()" style="background: white !important">
          </form>
            <div class="radio mb-3">
              <label><input class="form-check-input nodirty align-text-bottom ng-pristine ng-untouched ng-valid ng-not-empty" type="radio" data-ng-model="edit_mode" name="optradio" value="0" data-ng-change="changeEdit()">
                Set to <input type="number" class="form-control d-inline ng-pristine ng-untouched ng-valid ng-empty" data-ng-model="edit_set" data-ng-change="changeEdit()" data-ng-focus="edit_mode=0" style="width:8rem; background: white !important"></label>
            </div>
            <div class="radio mb-3">
              <label><input class="form-check-input nodirty align-text-bottom ng-pristine ng-untouched ng-valid ng-not-empty" type="radio" data-ng-model="edit_mode" name="optradio" value="1" data-ng-change="changeEdit()">
                Increase by <input type="number" class="form-control d-inline ng-pristine ng-untouched ng-valid ng-empty" data-ng-change="changeEdit()" data-ng-focus="edit_mode=1" data-ng-model="edit_inc" style="width:8rem; background: white !important"></label>
            </div>
            <div class="radio mb-3">
              <label><input class="form-check-input nodirty align-text-bottom ng-pristine ng-untouched ng-valid ng-not-empty" type="radio" data-ng-model="edit_mode" name="optradio" value="2" data-ng-change="changeEdit()">
                Increase by <input type="number" class="form-control d-inline ng-pristine ng-untouched ng-valid ng-empty" data-ng-change="changeEdit()" data-ng-focus="edit_mode=2" data-ng-model="edit_inc_perc" style="width:3rem; background: white !important"> %</label>
            </div>

          </td>
        </tr>
        </tbody></table>
      <!-- <div class="col-12">
      <label for="comment">Comment:</label>
      <textarea class="form-control" rows="3" id="comment" ng-model="edit_comment"></textarea>
      </div> -->
    </div>
  </div>
</template>

<style scoped>

</style>
